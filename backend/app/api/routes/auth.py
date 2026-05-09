from fastapi import APIRouter, Depends

from ...core.auth import AuthedUser, get_current_user


router = APIRouter()


@router.get('/auth/me')
async def me(user: AuthedUser = Depends(get_current_user)) -> dict:
    return {
        'email': user.email,
        'name': user.name,
        'picture': user.picture,
        'enabled': user.enabled,
        'role': user.role,
        'limits': {
            'summariesTotalLimit': user.summaries_total_limit,
            'summariesTotalUsed': user.summaries_total_used,
        },
    }

