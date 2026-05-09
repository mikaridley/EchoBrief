"""HTTP route for text-only summarization."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi import Depends

from ...core.config import get_settings
from ...core.auth import consume_summary_quota, AuthedUser
from ...schemas.meeting import ProcessResponse
from ...services import SummarizationError, summarize_transcript


router = APIRouter()


class SummarizeRequest(BaseModel):
    transcript: str = Field(min_length=1)


@router.post('/summarize', response_model=ProcessResponse)
async def summarize_text(
    payload: SummarizeRequest,
    _user: AuthedUser = Depends(consume_summary_quota),
) -> ProcessResponse:
    settings = get_settings()

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail='Missing OPENAI_API_KEY. Set it in backend/.env',
        )

    if not settings.summarization_enabled:
        return ProcessResponse(
            transcript=payload.transcript,
            summary='(dev) Summarization disabled (SUMMARIZATION_ENABLED=0).',
            participants=[],
            decisions=[],
            action_items=[],
            language=None,
            meta={'duration_sec': None, 'model_versions': {'whisper': None, 'llm': None}},
        )

    try:
        sr = await run_in_threadpool(
            summarize_transcript,
            transcript=payload.transcript,
            openai_api_key=settings.openai_api_key,
            model=settings.openai_summarize_model,
            timeout_sec=settings.openai_timeout_sec,
            cache_dir=settings.summarization_cache_dir,
            max_calls_per_min=settings.summarization_max_calls_per_min,
            prompt_version=settings.summarization_prompt_version,
            retry_on_invalid_json=settings.summarization_retry_on_invalid_json,
            rewrite_on_language_mismatch=settings.summarization_rewrite_on_language_mismatch,
        )
    except SummarizationError as e:
        if e.code == 'local_rate_limited':
            raise HTTPException(status_code=429, detail=str(e)) from e
        raise HTTPException(status_code=502, detail=f'summarization_failed: {str(e)}') from e

    return ProcessResponse(
        transcript=payload.transcript,
        summary=sr.summary,
        participants=sr.participants,
        decisions=sr.decisions,
        action_items=sr.action_items,
        language=None,
        meta={
            'duration_sec': None,
            'model_versions': {'whisper': None, 'llm': sr.model},
            'cached': sr.cached,
            'cached_summary': sr.cached,
        },
    )

