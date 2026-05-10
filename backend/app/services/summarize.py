"""
LLM transcript summarization service.

Cost constraint (project requirement):
- Default behavior is **one provider call per cache miss**.
- Extra calls (JSON-fix retry, language rewrite) are opt-in via flags.

This module also implements a best-effort on-disk cache to prevent repeated paid calls
for identical inputs.
"""

import hashlib
import json
import logging
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from ..paths import resolve_backend_path
from ..schemas.meeting import ActionItem


logger = logging.getLogger(__name__)

_recent_summarize_calls: list[float] = []

_DEFAULT_PROMPT_VERSION = '2026-05-08-3'


@dataclass(frozen=True)
class SummaryResult:
    summary: str
    participants: list[str]
    decisions: list[str]
    action_items: list[ActionItem]
    model: str
    cached: bool = False


def _summary_result_to_json_dict(result: SummaryResult) -> dict:
    """Match LLM JSON shape (summary / participants / decisions / action_items)."""
    return {
        'summary': result.summary,
        'participants': result.participants,
        'decisions': result.decisions,
        'action_items': [i.model_dump() for i in result.action_items],
    }


class SummarizationError(Exception):
    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _normalize_transcript_for_cache(transcript: str) -> str:
    # Conservative normalization: stable hash without changing content meaning.
    # - unify line endings
    # - trim trailing whitespace
    # - trim surrounding whitespace
    t = (transcript or '').replace('\r\n', '\n').replace('\r', '\n')
    t = '\n'.join(line.rstrip() for line in t.split('\n'))
    return t.strip()


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
        '### Speaker Identification\n'
        'First, estimate how many distinct people ACTIVELY SPEAK in the transcript (using conversational cues like turn-taking, "I" vs "you", first-person statements, agreements, questions, etc.).\n'
        'Then label each active speaker:\n'
        '- Use a real name ONLY when the speaker is self-introduced (e.g. "Hi, I\'m Tom") OR strongly implied by context (e.g. directly addressed by name and they reply, or clearly the narrator/host of the recording).\n'
        '- Otherwise use placeholders in first-speak order: "Speaker 1", "Speaker 2", "Speaker 3", ...\n'
        'If the transcript has any content, "participants" MUST contain at least one item (there is always at least one speaker).\n'
        '\n'
        '### Participant Filtering (CRITICAL)\n'
        'STRICT RULE: A participant is ONLY someone who has spoken lines in the transcript. '
        'If a person is mentioned as "absent", "missing", or is discussed in the third person '
        '(e.g., "Frank is not here"), DO NOT include them in the participants list.\n'
        '"participants" must include ONLY people who actively speak in the transcript.\n'
        'Do NOT include third parties that are only mentioned, referred to in third person, or teams/companies/departments.\n'
        'Example: if the narrator says "my brother Tom attends every meeting", Tom is NOT a participant unless Tom himself speaks in the transcript.\n'
        '\n'
        '### Decisions\n'
        '"decisions" must include only decisions explicitly made in the transcript. Otherwise return [].\n'
        '\n'
        '### Action Items (Ownership)\n'
        '"owner" is whoever must **perform** the task (the doer), not someone who is only mentioned as the target of contact.\n'
        '- CRITICAL: If the task is phrased like "talk to Dan", "call Sarah", "email the vendor", "ping the manager", the **mission** is for someone else to reach out. The owner is the person who must do that outreach (e.g. the speaker who said "I will", or whoever was assigned in the same exchange), NOT Dan/Sarah/the vendor unless the transcript clearly assigns the work to them.\n'
        '- Example: "I\'ll talk to Dan about the assets" → owner is the speaker (use their name from context or a matching "Speaker N" from participants), NOT "Dan".\n'
        '- The owner MAY be an active participant from "participants" when they are the one who must act.\n'
        '- The owner MAY be a third-party person or role only when the transcript clearly assigns **that** person or role to **do** the work (e.g. "Rich keeps the paper out there" → "Rich"; "the production manager will fix it" → "the production manager").\n'
        '- NEVER invent a name or role that is not present or strongly implied in the transcript.\n'
        '- If the doer cannot be identified, set "owner": null (never use the contact-only person as owner for "talk to X" tasks).\n'
        '- If no due date is explicitly stated, set "due": null.\n'
        '\n'
        '### Integrity checks (MUST satisfy)\n'
        '- "participants" contains only people with spoken lines in the transcript (not absent/missing/mentioned-only).\n'
        '- Every action_items[].owner is either null OR the person/role who must **perform** the task; never use someone who is only the object of "talk to / call / email" unless they are clearly assigned to do the work.\n'
        '- Output JSON matches the schema exactly, with no extra keys.\n'
        '\n'
        '### Transcript\n'
        f'{transcript}\n'
    )


def _cache_key_for_transcript(transcript: str) -> str:
    return hashlib.sha256(transcript.encode('utf-8')).hexdigest()


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _read_attempts_file(cache_path: Path) -> dict | None:
    """
    Read an attempts-history file. Expected shape:
        { "transcript_hash": "...", "attempts": [ {...}, ... ] }
    Returns None if missing, unreadable, or wrong shape.
    """
    try:
        data = json.loads(cache_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None
    attempts = data.get('attempts')
    if not isinstance(attempts, list):
        return None
    return data


def _find_matching_attempt(attempts: list[dict], *, model: str, prompt_version: str) -> dict | None:
    # Return the LAST attempt matching (model, prompt_version), or None.
    match: dict | None = None
    for a in attempts:
        if not isinstance(a, dict):
            continue
        if str(a.get('model') or '') == model and str(a.get('prompt_version') or '') == prompt_version:
            match = a
    return match


def _write_attempts_file(cache_path: Path, payload: dict) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            delete=False,
            dir=str(cache_path.parent),
            prefix=f'{cache_path.stem}.',
            suffix='.tmp',
        ) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(json.dumps(payload, ensure_ascii=False, indent=2))
        tmp_path.replace(cache_path)
    finally:
        if tmp_path and tmp_path.exists() and tmp_path != cache_path:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError as e:
                logger.warning(
                    'Failed to remove summarize cache temp file %s: %s',
                    tmp_path,
                    e,
                )


def _append_attempt(cache_path: Path, *, transcript_hash: str, attempt: dict) -> None:
    existing = _read_attempts_file(cache_path)
    if existing is None:
        existing = {'transcript_hash': transcript_hash, 'attempts': []}
    existing['transcript_hash'] = transcript_hash
    existing.setdefault('attempts', []).append(attempt)
    _write_attempts_file(cache_path, existing)


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


def _enforce_participants_non_empty(*, transcript: str, result: SummaryResult) -> SummaryResult:
    """
    Safety net:
    - Trust the LLM's participants list (it does the speaker-count inference).
    - Dedupe + drop empty strings.
    - If the list is empty but the transcript has content, fall back to ["Speaker 1"]
      (there is always at least one speaker).
    - action_items[].owner is trusted as-is (the prompt forbids invented names);
      we only normalize whitespace and let the LLM decide between participant,
      third-party name/role, or null.
    """
    seen: set[str] = set()
    deduped: list[str] = []
    for p in result.participants:
        name = (p or '').strip()
        if not name or name in seen:
            continue
        seen.add(name)
        deduped.append(name)

    if not deduped and transcript.strip():
        deduped = ['Speaker 1']

    cleaned_items: list[ActionItem] = []
    for item in result.action_items:
        owner_raw = (item.owner or '').strip()
        owner = owner_raw or None
        cleaned_items.append(ActionItem(task=item.task, owner=owner, due=item.due))

    return SummaryResult(
        summary=result.summary,
        participants=deduped,
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
    prompt_version: str = _DEFAULT_PROMPT_VERSION,
    retry_on_invalid_json: bool = False,
    rewrite_on_language_mismatch: bool = False,
) -> SummaryResult:
    """
    Summarize a transcript using an LLM, with caching to minimize paid calls.

    Call behavior:
    - Cache hit: **0** provider calls.
    - Cache miss: **1** provider call.
    - Optional: +1 call to fix invalid JSON (`retry_on_invalid_json=True`)
    - Optional: +1 call to rewrite language (`rewrite_on_language_mismatch=True`)
    """
    transcript_clean = _normalize_transcript_for_cache(transcript)
    if not transcript_clean:
        raise SummarizationError('Transcript is empty', code='empty_transcript')

    transcript_hash = _cache_key_for_transcript(transcript_clean)
    cache_root = resolve_backend_path(cache_dir)
    cache_path = cache_root / f'{transcript_hash}.json'

    file_data = _read_attempts_file(cache_path) if cache_path.exists() else None
    if file_data is not None:
        match = _find_matching_attempt(
            file_data.get('attempts') or [],
            model=model,
            prompt_version=prompt_version,
        )
        if match is not None:
            try:
                payload = {
                    'summary': match.get('summary'),
                    'participants': match.get('participants'),
                    'decisions': match.get('decisions'),
                    'action_items': match.get('action_items'),
                }
                result = _parse_and_validate(json.dumps(payload, ensure_ascii=False))
            except SummarizationError:
                # Bad attempt entry — ignore it and fall through to a fresh call.
                pass
            else:
                if not (
                    rewrite_on_language_mismatch
                    and _language_mismatch(transcript=transcript_clean, result=result)
                ):
                    return SummaryResult(
                        summary=result.summary,
                        participants=result.participants,
                        decisions=result.decisions,
                        action_items=result.action_items,
                        model=model,
                        cached=True,
                    )

    # Best-effort local dev rate limit (not reliable in multi-worker prod)
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
        if not retry_on_invalid_json:
            raise e

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

    if rewrite_on_language_mismatch and _language_mismatch(transcript=transcript_clean, result=parsed):
        language_name = _guess_language_name(transcript_clean)
        rewrite_res = client.responses.create(
            model=model,
            input=(
                f'Rewrite the following JSON so that ALL string values are in {language_name}.\n'
                'Keep the exact same JSON keys and structure.\n'
                'Return ONLY valid JSON.\n\n'
                f'JSON:\n{json.dumps(_summary_result_to_json_dict(parsed), ensure_ascii=False)}\n'
            ),
            store=False,
        )
        rewritten_text = (rewrite_res.output_text or '').strip()
        parsed = _parse_and_validate(rewritten_text)

    parsed = _enforce_participants_non_empty(transcript=transcript_clean, result=parsed)

    _append_attempt(
        cache_path,
        transcript_hash=transcript_hash,
        attempt={
            'model': model,
            'prompt_version': prompt_version,
            'created_at': _now_iso_utc(),
            **_summary_result_to_json_dict(parsed),
        },
    )

    return SummaryResult(
        summary=parsed.summary,
        participants=parsed.participants,
        decisions=parsed.decisions,
        action_items=parsed.action_items,
        model=model,
        cached=False,
    )

