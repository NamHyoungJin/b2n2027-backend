"""관리자 JWT 발급 (PyJWT)."""
from __future__ import annotations

import time
from datetime import datetime, timezone as dt_timezone

import jwt
from django.conf import settings

from apps.admin_accounts.models import AdminMemberShip


def create_admin_member_jwt_tokens(user: AdminMemberShip) -> dict:
    """Access + Refresh JWT 생성. token_issued_at 갱신으로 이전 토큰 무효화 추적."""
    now_ts = int(time.time())
    access_exp = now_ts + int(settings.JWT_ACCESS_EXPIRATION_DELTA)
    refresh_exp = now_ts + int(settings.JWT_REFRESH_EXPIRATION_DELTA)

    # JWT iat와 동일한 시각으로 저장해 무효화 비교 시 오판 방지
    user.token_issued_at = datetime.fromtimestamp(now_ts, tz=dt_timezone.utc)
    user.save(update_fields=["token_issued_at"])

    access_payload = {
        "user_id": str(user.memberShipSid),
        "exp": access_exp,
        "iat": now_ts,
        "site": "admin_api",
        "token_type": "access",
    }
    refresh_payload = {
        "user_id": str(user.memberShipSid),
        "exp": refresh_exp,
        "iat": now_ts,
        "site": "admin_api",
        "token_type": "refresh",
    }

    access_token = jwt.encode(
        access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    refresh_token = jwt.encode(
        refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    if isinstance(access_token, bytes):
        access_token = access_token.decode("utf-8")
    if isinstance(refresh_token, bytes):
        refresh_token = refresh_token.decode("utf-8")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": int(settings.JWT_ACCESS_EXPIRATION_DELTA),
    }
