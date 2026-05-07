import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from ..schemas.meeting import ActionItem


_recent_summarize_calls: list[float] = []


@dataclass(frozen=True)
class SummaryResult:
    summary: str
    participants: list[str]
    decisions: list[str]
    action_items: list[ActionItem]
    model: str
    cached: bool = False


class SummarizationError(Exception):
    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _infer_participants_from_transcript(transcript: str) -> list[str]:
    # Prefer explicit speaker labels when present (e.g. "Speaker 1:", "SPEAKER_00:", etc.)
    patterns = [
        r'^\s*(Speaker\s*\d+)\s*:',
        r'^\s*(SPEAKER[_\s-]*\d+)\s*:',
    ]

    found: list[str] = []
    for pat in patterns:
        for m in re.finditer(pat, transcript, flags=re.MULTILINE | re.IGNORECASE):
            label = (m.group(1) or '').strip()
            if not label:
                continue
            normalized = re.sub(r'\s+', ' ', label)
            normalized = normalized.upper().replace('SPEAKER_', 'SPEAKER ')
            normalized = normalized.title() if normalized.lower().startswith('speaker ') else normalized
            if normalized not in found:
                found.append(normalized)

    return found


def _guess_language_name(text: str) -> str:
    """
    Very small heuristic to reduce language-mismatch.
    We only need a "best guess" to push the model harder.
    """
    s = (text or '').lower()
    if not s:
        return 'English'

    es_hits = 0
    for w in (' el ', ' la ', ' los ', ' las ', ' de ', ' y ', ' que ', ' se ', ' por ', ' para ', ' con ', ' una '):
        if w in f' {s} ':
            es_hits += 1

    en_hits = 0
    for w in (' the ', ' and ', ' to ', ' of ', ' we ', ' you ', ' i ', ' is ', ' are ', ' for ', ' with '):
        if w in f' {s} ':
            en_hits += 1

    if es_hits >= en_hits + 2:
        return 'Spanish'
    return 'English'


def _is_spanish_like(text: str) -> bool:
    s = (text or '').lower()
    if not s:
        return False
    return any(w in f' {s} ' for w in (' el ', ' la ', ' los ', ' las ', ' de ', ' y ', ' que ', ' se '))


def _is_english_like(text: str) -> bool:
    s = (text or '').lower()
    if not s:
        return False
    return any(w in f' {s} ' for w in (' the ', ' and ', ' to ', ' of ', ' we ', ' you ', ' is ', ' are '))


def _language_mismatch(*, transcript: str, result: SummaryResult) -> bool:
    transcript_lang = _guess_language_name(transcript)
    blob = ' '.join(
        [
            result.summary,
            ' '.join(result.decisions),
            ' '.join(i.task for i in result.action_items),
            ' '.join((i.due or '') for i in result.action_items),
        ]
    )

    if transcript_lang == 'English':
        return _is_spanish_like(blob) and _is_english_like(transcript)  # clear mismatch
    if transcript_lang == 'Spanish':
        return _is_english_like(blob) and _is_spanish_like(transcript)  # clear mismatch
    return False


def _make_prompt(transcript: str) -> str:
    # Keep this prompt in sync with plan/003-phase-3-plan-with-prompt.md
    language_name = _guess_language_name(transcript)
    return (
        '### Role\n'
        'You are an expert Executive Assistant and Meeting Analyst. Your goal is to extract high-value insights from meeting transcripts with 100% accuracy.\n'
        '\n'
        '### Task\n'
        'Analyze the provided transcript and return a structured summary, participants, decisions, and action items.\n'
        '\n'
        '### Language\n'
        f'The transcript language is: {language_name}.\n'
        f'You MUST write ALL JSON string values in {language_name}. Do NOT translate to any other language.\n'
        '\n'
        '### Output Format (STRICT)\n'
        'Output ONLY a valid JSON object and nothing else.\n'
        'Do NOT include conversational text.\n'
        'Do NOT use markdown or code fences (do NOT output ```json).\n'
        'Do NOT add any extra top-level keys or nested keys beyond the schema.\n'
        '\n'
        'Schema (EXACT):\n'
        '{\n'
        '  "summary": string,\n'
        '  "participants": string[],\n'
        '  "decisions": string[],\n'
        '  "action_items": [{"task": string, "owner": string|null, "due": string|null}]\n'
        '}\n'
        '\n'
        '### Speaker Identification (NO GUESSING)\n'
        'Participants MUST be derived ONLY from transcript speaker labels (active speakers).\n'
        'Never infer or fabricate names from context.\n'
        'If real names are not explicitly present as speaker labels, use placeholders exactly: "Speaker 1", "Speaker 2", etc.\n'
        '\n'
        '### Participant Filtering (CRITICAL)\n'
        '"participants" must include ONLY people who actively speak in the transcript.\n'
        'Do NOT include third parties that are only mentioned, referred to in third person, or teams/companies/departments.\n'
        '\n'
        '### Decisions\n'
        '"decisions" must include only decisions explicitly made in the transcript. Otherwise return [].\n'
        '\n'
        '### Action Items (Ownership constraints)\n'
        'Action items can ONLY be assigned to an active participant from the "participants" list.\n'
        'If an action mentions a third party (e.g., "Talk to Rotem"), the owner MUST be the meeting participant responsible for contacting them, not the third party.\n'
        'If no owner is explicitly assigned to an active participant, set "owner": null.\n'
        'If no due date is explicitly stated, set "due": null.\n'
        '\n'
        '### Integrity checks (MUST satisfy)\n'
        '- Every action_items[].owner is either null OR exactly one of "participants".\n'
        '- "participants" contains only active speakers.\n'
        '- Output JSON matches the schema exactly, with no extra keys.\n'
        '\n'
        '### Transcript\n'
        f'{transcript}\n'
    )


def _parse_and_validate(payload_text: str) -> SummaryResult:
    try:
        data = json.loads(payload_text)
    except json.JSONDecodeError as e:
        raise SummarizationError('Invalid JSON', code='invalid_json') from e

    if not isinstance(data, dict):
        raise SummarizationError('JSON must be an object', code='invalid_json')

    allowed = {'summary', 'participants', 'decisions', 'action_items'}
    extra = set(data.keys()) - allowed
    if extra:
        raise SummarizationError(f'JSON has extra keys: {sorted(extra)}', code='invalid_json')

    try:
        summary = str(data.get('summary') or '').strip()
        participants = list(data.get('participants') or [])
        decisions = list(data.get('decisions') or [])
        raw_items = list(data.get('action_items') or [])
        action_items = [ActionItem.model_validate(x) for x in raw_items]
    except (TypeError, ValidationError) as e:
        raise SummarizationError('JSON does not match schema', code='schema_mismatch') from e

    if not summary:
        raise SummarizationError('Summary is empty', code='schema_mismatch')

    participants = [str(p).strip() for p in participants if str(p).strip()]
    decisions = [str(d).strip() for d in decisions if str(d).strip()]

    return SummaryResult(
        summary=summary,
        participants=participants,
        decisions=decisions,
        action_items=action_items,
        model='',
        cached=False,
    )


def _enforce_speaker_only_participants(*, transcript: str, result: SummaryResult) -> SummaryResult:
    """
    Safety net against hallucinated participants / owners:
    - participants can only be active speaker labels in the transcript
    - action item owners can only be participants (else null)
    """
    speaker_labels = _infer_participants_from_transcript(transcript)
    allowed = set(speaker_labels)

    filtered_participants = [p for p in result.participants if p in allowed]
    if not filtered_participants and speaker_labels:
        filtered_participants = speaker_labels

    filtered_allowed = set(filtered_participants)
    cleaned_items: list[ActionItem] = []
    for item in result.action_items:
        owner = item.owner if (item.owner and item.owner in filtered_allowed) else None
        cleaned_items.append(ActionItem(task=item.task, owner=owner, due=item.due))

    return SummaryResult(
        summary=result.summary,
        participants=filtered_participants,
        decisions=result.decisions,
        action_items=cleaned_items,
        model=result.model,
        cached=result.cached,
    )


def summarize_transcript(
    *,
    transcript: str,
    openai_api_key: str,
    model: str = 'gpt-5.4-mini',
    timeout_sec: float = 60.0,
    cache_dir: str | Path = 'backend/.cache/summaries',
    max_calls_per_min: int = 10,
) -> SummaryResult:
    transcript_clean = (transcript or '').strip()
    if not transcript_clean:
        raise SummarizationError('Transcript is empty', code='empty_transcript')

    h = hashlib.sha256(transcript_clean.encode('utf-8')).hexdigest()
    cache_root = Path(cache_dir)
    cache_path = cache_root / f'{h}.json'
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding='utf-8'))
        try:
            payload = {
                'summary': cached.get('summary'),
                'participants': cached.get('participants'),
                'decisions': cached.get('decisions'),
                'action_items': cached.get('action_items'),
            }
            result = _parse_and_validate(json.dumps(payload, ensure_ascii=False))
        except SummarizationError:
            cache_path.unlink(missing_ok=True)
        else:
            if _language_mismatch(transcript=transcript_clean, result=result):
                cache_path.unlink(missing_ok=True)
            else:
                return SummaryResult(
                    summary=result.summary,
                    participants=result.participants,
                    decisions=result.decisions,
                    action_items=result.action_items,
                    model=str(cached.get('model') or model),
                    cached=True,
                )

    now = time.time()
    cutoff = now - 60
    while _recent_summarize_calls and _recent_summarize_calls[0] < cutoff:
        _recent_summarize_calls.pop(0)
    if len(_recent_summarize_calls) >= max_calls_per_min:
        raise SummarizationError('Local dev rate limit hit', code='local_rate_limited')
    _recent_summarize_calls.append(now)

    client = OpenAI(api_key=openai_api_key, timeout=timeout_sec)

    prompt = _make_prompt(transcript_clean)
    res = client.responses.create(
        model=model,
        input=prompt,
        store=False,
    )

    text = (res.output_text or '').strip()
    if not text:
        raise SummarizationError('Empty response from model', code='provider_error')

    try:
        parsed = _parse_and_validate(text)
    except SummarizationError as e:
        # One retry: ask the model to fix JSON only.
        fix_res = client.responses.create(
            model=model,
            input=(
                'Fix the following output to be ONLY valid JSON matching the schema.\n'
                'Do not add extra keys.\n\n'
                f'Bad output:\n{text}\n'
            ),
            store=False,
        )
        fixed_text = (fix_res.output_text or '').strip()
        parsed = _parse_and_validate(fixed_text)

    if _language_mismatch(transcript=transcript_clean, result=parsed):
        language_name = _guess_language_name(transcript_clean)
        rewrite_res = client.responses.create(
            model=model,
            input=(
                f'Rewrite the following JSON so that ALL string values are in {language_name}.\n'
                'Keep the exact same JSON keys and structure.\n'
                'Return ONLY valid JSON.\n\n'
                f'JSON:\n{json.dumps(parsed.model_dump(), ensure_ascii=False)}\n'
            ),
            store=False,
        )
        rewritten_text = (rewrite_res.output_text or '').strip()
        parsed = _parse_and_validate(rewritten_text)

    parsed = _enforce_speaker_only_participants(transcript=transcript_clean, result=parsed)

    cache_root.mkdir(parents=True, exist_ok=True)
    cache_root.joinpath(f'{h}.json').write_text(
        json.dumps(
            {
                'summary': parsed.summary,
                'participants': parsed.participants,
                'decisions': parsed.decisions,
                'action_items': [i.model_dump() for i in parsed.action_items],
                'model': model,
            },
            ensure_ascii=False,
        ),
        encoding='utf-8',
    )

    return SummaryResult(
        summary=parsed.summary,
        participants=parsed.participants,
        decisions=parsed.decisions,
        action_items=parsed.action_items,
        model=model,
        cached=False,
    )

