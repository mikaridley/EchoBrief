import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token

from ..repositories import UsersRepository
from .config import get_settings
from .db import get_db_from_app

# Effective "unlimited" cap for admins and local auth-off dev (not incremented for admins).
ADMIN_SUMMARIES_TOTAL_LIMIT = 10**9


@dataclass(frozen=True)
class AuthedUser:
    email: str
    name: str | None = None
    picture: str | None = None
    enabled: bool = False
    role: str | None = None
    summaries_total_limit: int = 5
    summaries_total_used: int = 0


def _extract_bearer_token(request: Request) -> str | None:
    auth = request.headers.get('authorization') or ''
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        return parts[1].strip() or None
    return None


def _verify_google_id_token_sync(token: str, google_client_id: str) -> dict:
    # This verifies signature, expiry, issuer, etc.
    # audience check (client_id) is critical.
    return google_id_token.verify_oauth2_token(token, GoogleRequest(), google_client_id)


async def get_current_user(request: Request) -> AuthedUser:
    settings = get_settings()
    if not settings.auth_enabled:
        # Safety: never allow "open admin" behavior outside local dev.
        if not settings.is_local:
            raise HTTPException(
                status_code=500,
                detail={
                    'code': 'AUTH_DISABLED',
                    'message': 'AUTH_ENABLED=0 is only allowed in ENV=local',
                },
            )
        return AuthedUser(
            email='dev@local',
            enabled=True,
            role='admin',
            summaries_total_limit=ADMIN_SUMMARIES_TOTAL_LIMIT,
        )

    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail='Missing GOOGLE_CLIENT_ID. Set it in backend/.env')

    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail={'code': 'UNAUTHENTICATED', 'message': 'Missing bearer token'})

    try:
        payload = await run_in_threadpool(_verify_google_id_token_sync, token, settings.google_client_id)
    except Exception:
        raise HTTPException(status_code=401, detail={'code': 'UNAUTHENTICATED', 'message': 'Invalid token'})

    email = str(payload.get('email') or '').strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail={'code': 'UNAUTHENTICATED', 'message': 'Token missing email'})

    name = payload.get('name')
    picture = payload.get('picture')

    repo = UsersRepository(get_db_from_app(request.app))

    now = int(time.time())
    base_limit = int(settings.summaries_total_limit_default)

    doc = await repo.find_by_email(email)
    if doc is None:
        await repo.insert_google_user(
            email=email,
            name=name,
            picture=picture,
            base_limit=base_limit,
            now=now,
        )
        enabled = False
        role = 'user'
        limit = base_limit
        used = 0
    else:
        await repo.update_google_profile_on_login(
            user_id=doc['_id'],
            name=name,
            picture=picture,
            now=now,
            base_limit=base_limit,
        )
        enabled = bool(doc.get('enabled', False))
        role = doc.get('role')
        limits = doc.get('limits') or {}
        limit = int(limits.get('summariesTotalLimit', base_limit))
        used = int(limits.get('summariesTotalUsed', 0))

    if role == 'admin':
        limit = ADMIN_SUMMARIES_TOTAL_LIMIT

    return AuthedUser(
        email=email,
        name=name,
        picture=picture,
        enabled=enabled,
        role=role,
        summaries_total_limit=limit,
        summaries_total_used=used,
    )


async def require_enabled_user(user: AuthedUser = Depends(get_current_user)) -> AuthedUser:
    if not user.enabled:
        raise HTTPException(
            status_code=403,
            detail={'code': 'ACCESS_REQUIRED', 'message': 'Access required. Contact admin.'},
        )
    return user


async def consume_summary_quota(request: Request, user: AuthedUser = Depends(require_enabled_user)) -> AuthedUser:
    if user.role == 'admin':
        return AuthedUser(
            email=user.email,
            name=user.name,
            picture=user.picture,
            enabled=True,
            role=user.role,
            summaries_total_limit=ADMIN_SUMMARIES_TOTAL_LIMIT,
            summaries_total_used=user.summaries_total_used,
        )

    # Atomically increments used count if still below limit.
    repo = UsersRepository(get_db_from_app(request.app))

    res = await repo.try_increment_summary_usage(user.email)

    if not res:
        # Either user disabled or quota exceeded
        current = await repo.find_by_email(user.email)
        if current and not current.get('enabled', False):
            raise HTTPException(
                status_code=403,
                detail={'code': 'ACCESS_REQUIRED', 'message': 'Access required. Contact admin.'},
            )

        raise HTTPException(
            status_code=403,
            detail={'code': 'QUOTA_EXCEEDED', 'message': 'Quota exceeded (5 total summaries).'},
        )

    limits = res.get('limits') or {}
    return AuthedUser(
        email=user.email,
        name=user.name,
        picture=user.picture,
        enabled=True,
        role=res.get('role'),
        summaries_total_limit=int(limits.get('summariesTotalLimit', user.summaries_total_limit)),
        summaries_total_used=int(limits.get('summariesTotalUsed', user.summaries_total_used + 1)),
    )

