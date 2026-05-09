from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ...core.auth import require_enabled_user, AuthedUser
from ...schemas.meeting import DocxRequest
from ...services.docx import build_docx_bytes


router = APIRouter()


@router.post('/docx')
def create_docx(
    payload: DocxRequest,
    _user: AuthedUser = Depends(require_enabled_user),
) -> StreamingResponse:
    docx_bytes = build_docx_bytes(payload)

    headers = {'Content-Disposition': 'attachment; filename="meeting-summary.docx"'}
    return StreamingResponse(
        iter([docx_bytes]),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers=headers,
    )

