import os
import tempfile
import logging
from dataclasses import dataclass
from pathlib import Path

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)


ALLOWED_AUDIO_EXTS = {'.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm'}

logger = logging.getLogger(__name__)

def _safe_provider_details(e: Exception) -> str:
    parts: list[str] = [type(e).__name__]
    status = getattr(e, 'status_code', None)
    if status is not None:
        parts.append(f'status={status}')

    resp = getattr(e, 'response', None)
    if resp is not None:
        try:
            text = getattr(resp, 'text', None)
            if text:
                parts.append(f'response={text}')
        except Exception:
            pass

    msg = str(e).strip()
    if msg:
        parts.append(f'message={msg}')

    return ' | '.join(parts)


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    language: str | None = None
    model: str | None = None


class TranscriptionError(Exception):
    def __init__(self, message: str, *, code: str, provider_message: str | None = None):
        super().__init__(message)
        self.code = code
        self.provider_message = provider_message


def transcribe_audio(
    *,
    file_path: str | Path | None = None,
    file_bytes: bytes | None = None,
    filename: str | None = None,
    max_bytes: int | None = None,
    openai_api_key: str | None = None,
    model: str = 'whisper-1',
    timeout_sec: float = 60.0,
) -> TranscriptionResult:
    if (file_path is None) == (file_bytes is None):
        raise ValueError('Provide exactly one of file_path or file_bytes')

    inferred_name = filename
    if inferred_name is None and file_path is not None:
        inferred_name = Path(file_path).name

    if inferred_name:
        ext = Path(inferred_name).suffix.lower()
        if ext and ext not in ALLOWED_AUDIO_EXTS:
            raise TranscriptionError(
                f'Unsupported file type. Allowed: {", ".join(sorted(ALLOWED_AUDIO_EXTS))}',
                code='unsupported_format',
            )

    if file_bytes is not None and max_bytes is not None and len(file_bytes) > max_bytes:
        raise TranscriptionError('File too large', code='file_too_large')

    client = OpenAI(api_key=openai_api_key, timeout=timeout_sec)

    temp_path: str | None = None
    try:
        audio_path = Path(file_path) if file_path is not None else None

        if file_bytes is not None:
            suffix = Path(inferred_name or '').suffix or '.wav'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                temp_path = tmp.name
                tmp.write(file_bytes)
            audio_path = Path(temp_path)

        if audio_path is None:
            raise RuntimeError('Audio path resolution failed')

        if max_bytes is not None:
            try:
                size = audio_path.stat().st_size
            except OSError as e:
                logger.exception('Could not stat audio file for size check')
                raise TranscriptionError(
                    'Could not read audio file',
                    code='file_unreadable',
                    provider_message=str(e) or type(e).__name__,
                ) from e
            if size > max_bytes:
                raise TranscriptionError('File too large', code='file_too_large')

        with open(audio_path, 'rb') as f:
            try:
                res = client.audio.transcriptions.create(model=model, file=f)
            except APITimeoutError as e:
                logger.exception('Whisper timeout')
                raise TranscriptionError(
                    'Transcription timed out',
                    code='timeout',
                    provider_message=_safe_provider_details(e),
                ) from e
            except AuthenticationError as e:
                logger.exception('OpenAI auth failed')
                raise TranscriptionError(
                    'OpenAI authentication failed',
                    code='auth_failed',
                    provider_message=_safe_provider_details(e),
                ) from e
            except RateLimitError as e:
                logger.exception('OpenAI rate limited')
                raise TranscriptionError(
                    'Rate limited / quota exceeded on OpenAI',
                    code='rate_limited',
                    provider_message=_safe_provider_details(e),
                ) from e
            except APIConnectionError as e:
                logger.exception('OpenAI connection error')
                raise TranscriptionError(
                    'Failed to connect to OpenAI',
                    code='connection_error',
                    provider_message=_safe_provider_details(e),
                ) from e
            except APIStatusError as e:
                logger.exception('OpenAI status error')
                raise TranscriptionError(
                    'OpenAI returned an error',
                    code='provider_error',
                    provider_message=_safe_provider_details(e),
                ) from e
            except Exception as e:
                logger.exception('Unexpected transcription error')
                raise TranscriptionError(
                    'Transcription failed',
                    code='provider_error',
                    provider_message=_safe_provider_details(e),
                ) from e

        transcript = (getattr(res, 'text', None) or '').strip()
        language = getattr(res, 'language', None)
        if not transcript:
            raise TranscriptionError('Empty transcript returned', code='empty_transcript')

        return TranscriptionResult(transcript=transcript, language=language, model=model)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as e:
                logger.warning(
                    'Failed to remove temp audio file %s: %s',
                    temp_path,
                    e,
                )

