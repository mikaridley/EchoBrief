from fastapi import APIRouter, HTTPException
from openai import OpenAI

from ...core.config import get_settings


router = APIRouter()


@router.get('/openai/test')
def openai_test() -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail='Missing OPENAI_API_KEY')

    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_sec)
    try:
        res = client.responses.create(
            model='gpt-5.4-mini',
            input='write a haiku about ai',
            store=False,
        )
        return {'ok': True, 'output_text': res.output_text}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

