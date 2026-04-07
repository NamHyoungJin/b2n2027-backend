"""관리자 API — Bearer Access JWT."""
import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.admin_accounts.models import AdminMemberShip


class AdminJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return None

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("토큰이 만료되었습니다.") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed("유효하지 않은 토큰입니다.") from exc

        if payload.get("token_type") != "access" or payload.get("site") != "admin_api":
            raise AuthenticationFailed("잘못된 토큰 유형입니다.")

        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationFailed("토큰에 사용자 정보가 없습니다.")

        try:
            user = AdminMemberShip.objects.get(memberShipSid=user_id, is_active=True)
        except AdminMemberShip.DoesNotExist as exc:
            raise AuthenticationFailed("사용자를 찾을 수 없습니다.") from exc

        token_iat = payload.get("iat")
        if token_iat is not None and user.token_issued_at is not None:
            from datetime import datetime, timezone as dt_tz

            issued = datetime.fromtimestamp(int(token_iat), tz=dt_tz.utc)
            if issued < user.token_issued_at:
                raise AuthenticationFailed("토큰이 무효화되었습니다. 다시 로그인하세요.")

        return (user, token)
