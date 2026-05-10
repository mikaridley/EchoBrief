"""HTTP route for audio upload -> transcription (and optional summarization)."""

import os
import tempfile
import time
import json
import hashlib
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi import Depends

from ...core.config import get_settings
from ...paths import resolve_backend_path
from ...core.auth import consume_summary_quota, AuthedUser
from ...services import SummarizationError, TranscriptionError, summarize_transcript, transcribe_audio
from ...schemas.meeting import ActionItem, ProcessResponse


router = APIRouter()

ALLOWED_EXTS = {'.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm'}
_recent_transcribe_calls: list[float] = []


@router.post('/process', response_model=ProcessResponse)
async def process_audio(
    file: UploadFile = File(...),
    _user: AuthedUser = Depends(consume_summary_quota),
) -> ProcessResponse:
    settings = get_settings()

    if (settings.transcription_enabled or settings.summarization_enabled) and not settings.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail='Missing OPENAI_API_KEY. Set it in backend/.env',
        )

    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f'Unsupported file type. Allowed: {", ".join(sorted(ALLOWED_EXTS))}',
        )

    total = 0
    temp_path: str | None = None
    sha = hashlib.sha256()

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f'File too large. Max is {settings.max_upload_mb}MB',
                    )
                sha.update(chunk)
                tmp.write(chunk)

        file_hash = sha.hexdigest()
        cache_dir = resolve_backend_path(settings.transcription_cache_dir)
        cache_path = cache_dir / f'{file_hash}.json'
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding='utf-8'))
            tr_text = (cached.get('transcript') or '').strip()
            if tr_text:
                summary = ''
                participants: list[str] = []
                decisions: list[str] = []
                action_items: list[ActionItem] = []
                summarize_cached = False
                summarize_model: str | None = None

                if settings.summarization_enabled:
                    try:
                        sr = await run_in_threadpool(
                            summarize_transcript,
                            transcript=tr_text,
                            openai_api_key=settings.openai_api_key,
                            model=settings.openai_summarize_model,
                            timeout_sec=settings.openai_timeout_sec,
                            cache_dir=settings.summarization_cache_dir,
                            max_calls_per_min=(
                                settings.summarization_max_calls_per_min if settings.is_local else 10**9
                            ),
                            prompt_version=settings.summarization_prompt_version,
                            retry_on_invalid_json=settings.summarization_retry_on_invalid_json,
                            rewrite_on_language_mismatch=settings.summarization_rewrite_on_language_mismatch,
                        )
                        summary = sr.summary
                        participants = sr.participants
                        decisions = sr.decisions
                        action_items = sr.action_items
                        summarize_cached = sr.cached
                        summarize_model = sr.model
                    except SummarizationError as e:
                        if e.code == 'local_rate_limited':
                            raise HTTPException(status_code=429, detail=str(e)) from e
                        raise HTTPException(status_code=502, detail=f'summarization_failed: {str(e)}') from e

                return ProcessResponse(
                    transcript=tr_text,
                    summary=summary or 'Summarization disabled (SUMMARIZATION_ENABLED=0).',
                    participants=participants,
                    decisions=decisions,
                    action_items=action_items,
                    language=cached.get('language'),
                    meta={
                        'duration_sec': None,
                        'model_versions': {'whisper': cached.get('model'), 'llm': summarize_model},
                        'cached': True,
                        'cached_summary': summarize_cached,
                    },
                )

        if not settings.transcription_enabled:
            return ProcessResponse(
                transcript='Transcription disabled (TRANSCRIPTION_ENABLED=0).',
                summary='Summarization disabled (SUMMARIZATION_ENABLED=0).',
                participants=[],
                decisions=[],
                action_items=[],
                language=None,
                meta={'duration_sec': None, 'model_versions': {'whisper': None, 'llm': None}},
            )

        # Best-effort local dev rate limit (not reliable in multi-worker prod)
        if settings.is_local:
            now = time.time()
            cutoff = now - 60
            while _recent_transcribe_calls and _recent_transcribe_calls[0] < cutoff:
                _recent_transcribe_calls.pop(0)
            if len(_recent_transcribe_calls) >= settings.transcription_max_calls_per_min:
                raise HTTPException(
                    status_code=429,
                    detail='Local dev rate limit hit. Wait a minute or increase TRANSCRIPTION_MAX_CALLS_PER_MIN',
                )
            _recent_transcribe_calls.append(now)

        try:
            tr = await run_in_threadpool(
                transcribe_audio,
                file_path=temp_path,
                filename=file.filename,
                max_bytes=settings.max_upload_bytes,
                openai_api_key=settings.openai_api_key,
                model=settings.openai_whisper_model,
                timeout_sec=settings.openai_timeout_sec,
            )
        except TranscriptionError as e:
            if e.code == 'unsupported_format':
                raise HTTPException(status_code=400, detail=str(e)) from e
            if e.code == 'file_too_large':
                raise HTTPException(
                    status_code=413,
                    detail=f'File too large. Max is {settings.max_upload_mb}MB',
                ) from e
            if e.code == 'file_unreadable':
                raise HTTPException(status_code=400, detail=str(e)) from e
            if e.code == 'timeout':
                raise HTTPException(status_code=504, detail=str(e)) from e
            if e.code == 'auth_failed':
                raise HTTPException(
                    status_code=502,
                    detail=f'{str(e)}. Check OPENAI_API_KEY',
                ) from e
            if e.code == 'rate_limited':
                if e.provider_message:
                    raise HTTPException(status_code=429, detail=e.provider_message) from e
                raise HTTPException(status_code=429, detail=str(e)) from e
            if e.provider_message is not None:
                raise HTTPException(status_code=502, detail=e.provider_message or str(e)) from e
            raise HTTPException(status_code=502, detail=f'{e.code}: {str(e)}') from e

        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {'transcript': tr.transcript, 'language': tr.language, 'model': tr.model},
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )

        summary = ''
        participants: list[str] = []
        decisions: list[str] = []
        action_items: list[ActionItem] = []
        summarize_cached = False
        summarize_model: str | None = None

        if settings.summarization_enabled:
            if not settings.openai_api_key:
                raise HTTPException(status_code=500, detail='Missing OPENAI_API_KEY for summarization')

            try:
                sr = await run_in_threadpool(
                    summarize_transcript,
                    transcript=tr.transcript,
                    openai_api_key=settings.openai_api_key,
                    model=settings.openai_summarize_model,
                    timeout_sec=settings.openai_timeout_sec,
                    cache_dir=settings.summarization_cache_dir,
                    max_calls_per_min=(
                        settings.summarization_max_calls_per_min if settings.is_local else 10**9
                    ),
                    prompt_version=settings.summarization_prompt_version,
                    retry_on_invalid_json=settings.summarization_retry_on_invalid_json,
                    rewrite_on_language_mismatch=settings.summarization_rewrite_on_language_mismatch,
                )
                summary = sr.summary
                participants = sr.participants
                decisions = sr.decisions
                action_items = sr.action_items
                summarize_cached = sr.cached
                summarize_model = sr.model
            except SummarizationError as e:
                if e.code == 'local_rate_limited':
                    raise HTTPException(status_code=429, detail=str(e)) from e
                raise HTTPException(status_code=502, detail=f'summarization_failed: {str(e)}') from e

        return ProcessResponse(
            transcript=tr.transcript,
            summary=summary or 'Summarization disabled (SUMMARIZATION_ENABLED=0).',
            participants=participants,
            decisions=decisions,
            action_items=action_items,
            language=tr.language,
            meta={
                'duration_sec': None,
                'model_versions': {'whisper': tr.model, 'llm': summarize_model},
                'cached': False,
                'cached_summary': summarize_cached,
            },
        )
    finally:
        try:
            await file.close()
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

