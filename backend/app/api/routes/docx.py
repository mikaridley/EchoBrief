from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...schemas.meeting import DocxRequest
from ...services.docx import build_docx_bytes


router = APIRouter()


@router.post('/docx')
def create_docx(payload: DocxRequest) -> StreamingResponse:
    docx_bytes = build_docx_bytes(payload)

    headers = {'Content-Disposition': 'attachment; filename="meeting-summary.docx"'}
    return StreamingResponse(
        iter([docx_bytes]),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers=headers,
    )

