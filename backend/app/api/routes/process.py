import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.meeting import ActionItem, ProcessResponse


router = APIRouter()

ALLOWED_EXTS = {'.mp3', '.wav'}


@router.post('/process', response_model=ProcessResponse)
async def process_audio(file: UploadFile = File(...)) -> ProcessResponse:
    settings = get_settings()

    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f'Unsupported file type. Allowed: {", ".join(sorted(ALLOWED_EXTS))}',
        )

    total = 0
    temp_path: str | None = None

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
                tmp.write(chunk)

        return ProcessResponse(
            transcript='(stub) Transcript will be produced in Phase 2 (Whisper).',
            summary='(stub) Summary will be produced in Phase 3 (LLM).',
            participants=['Alice', 'Bob'],
            decisions=['Use FastAPI backend skeleton for Phase 1'],
            action_items=[
                ActionItem(task='Implement Whisper transcription service', owner='Backend', due=None),
                ActionItem(task='Implement LLM summarization service', owner='Backend', due=None),
            ],
            language='en',
            meta={'duration_sec': None, 'model_versions': {'whisper': None, 'llm': None}},
        )
    finally:
        try:
            await file.close()
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

