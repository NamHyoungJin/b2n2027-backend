"""
www `/apply` 등록 — 기존 신청자 없이 휴대폰 OTP 발송·검증 후 Participant 생성 시 서명 토큰으로 소유 확인.
"""

from __future__ import annotations

import logging
import secrets

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.mixins import B2nResponseMixin
from apps.messages.aligo_sms import send_mass_with_aligo
from apps.messages.models import get_default_sms_sender_number

from .public_confirmation import find_participant_by_phone, normalize_phone

logger = logging.getLogger(__name__)

REG_PHONE_OTP_PREFIX = "reg_phone_otp:"
REG_PHONE_SEND_COOLDOWN_PREFIX = "reg_phone_send:"
SIGN_SALT_REG = "b2n-register-phone-verify"
OTP_TTL = 600
SEND_COOLDOWN_SEC = 45
REG_TOKEN_MAX_AGE = 30 * 60


def _mask_phone(nd: str) -> str:
    if len(nd) >= 11:
        return f"{nd[:3]}-****-{nd[-4:]}"
    if len(nd) >= 8:
        return f"{nd[:2]}***{nd[-4:]}"
    return "****"


def sign_registration_phone_token(phone_nd: str) -> str:
    signer = signing.TimestampSigner(salt=SIGN_SALT_REG)
    return signer.sign(phone_nd)


def verify_registration_phone_token(token: str, phone_raw: str) -> bool:
    """Participant POST 시 `phone`과 서명 토큰 일치 여부."""
    nd = normalize_phone(phone_raw)
    if len(nd) < 10:
        return False
    t = (token or "").strip()
    if not t:
        return False
    try:
        signer = signing.TimestampSigner(salt=SIGN_SALT_REG)
        got = signer.unsign(t, max_age=REG_TOKEN_MAX_AGE)
        return got == nd
    except (signing.BadSignature, signing.SignatureExpired, ValueError):
        return False


class SendRegistrationSmsView(B2nResponseMixin, APIView):
    """등록용 — 이미 Participant가 있으면 거부(중복), 없으면 OTP 발송."""

    permission_classes = [AllowAny]

    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        nd = normalize_phone(phone)
        if len(nd) < 10:
            return Response(
                {"detail": "휴대폰 번호를 올바르게 입력해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 중복 번호면 SMS 발송 없이 즉시 거부 (쿨다운·OTP 생성 전)
        if find_participant_by_phone(phone) is not None:
            return Response(
                {"detail": "이미 등록된 핸드폰 번호입니다. 등록하실 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cooldown_key = f"{REG_PHONE_SEND_COOLDOWN_PREFIX}{nd}"
        if cache.get(cooldown_key):
            return Response(
                {"detail": "잠시 후 다시 인증번호를 요청해 주세요."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # 100000–999999 (항상 숫자 6자리)
        code = f"{secrets.randbelow(900000) + 100000}"
        cache_key = f"{REG_PHONE_OTP_PREFIX}{nd}"
        cache.set(cache_key, {"code": code}, OTP_TTL)
        cache.set(cooldown_key, 1, SEND_COOLDOWN_SEC)

        msg = f"[B2N2027] 등록 인증번호는 [{code}] 입니다. (10분 이내 입력)"

        sender = get_default_sms_sender_number()
        api_key = (getattr(settings, "ALIGO_API_KEY", "") or "").strip()
        user_id = (getattr(settings, "ALIGO_USER_ID", "") or "").strip()

        if not sender or not api_key or not user_id:
            if settings.DEBUG:
                logger.warning(
                    "[SMS REG] Aligo 미설정 — 개발용 코드 phone=%s code=%s",
                    nd,
                    code,
                )
            else:
                return Response(
                    {
                        "detail": "문자 발송 설정이 아직 완료되지 않았습니다. "
                        "관리자 페이지에서 알리고 연동 및 발신번호(승인완료) 등록을 확인해 주세요."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        else:
            send_result = send_mass_with_aligo(sender, "", [nd], [msg])
            if not send_result.get("ok"):
                logger.error("[SMS REG] 발송 실패: %s", send_result)
                return Response(
                    {
                        "detail": send_result.get("message")
                        or "인증 문자 발송에 실패했습니다. 잠시 후 다시 시도해 주세요.",
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(
            {
                "masked_phone": _mask_phone(nd),
                "expires_in": OTP_TTL,
                **({"dev_code": code} if settings.DEBUG else {}),
            }
        )


class VerifyRegistrationSmsView(B2nResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        code = (request.data.get("code") or "").strip().replace(" ", "")
        nd = normalize_phone(phone)
        if len(nd) < 10 or len(code) != 6 or not code.isdigit():
            return Response(
                {"detail": "휴대폰 번호와 인증번호 6자리를 입력해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = f"{REG_PHONE_OTP_PREFIX}{nd}"
        data = cache.get(cache_key)
        if not data or data.get("code") != code:
            return Response(
                {"detail": "인증번호가 올바르지 않거나 만료되었습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete(cache_key)
        token = sign_registration_phone_token(nd)
        return Response({"token": token})
