"""
공개 신청 확인 — 휴대폰 SMS 인증 후 본인 신청만 조회·수정 (상태: 신청중·신청확인중 만).
"""

from __future__ import annotations

import logging
import secrets

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.mixins import B2nResponseMixin
from apps.messages.aligo_sms import send_mass_with_aligo
from apps.messages.models import get_default_sms_sender_number

from apps.products.serializers import update_product_application_from_payload

from .models import Participant
from .serializers import ParticipantCreateSerializer, ParticipantSerializer

logger = logging.getLogger(__name__)

PHONE_OTP_PREFIX = "phone_otp:"
PHONE_SEND_COOLDOWN_PREFIX = "phone_otp_send:"
SIGN_SALT = "b2n-participant-phone-confirm"
OTP_TTL = 600  # 10분
SEND_COOLDOWN_SEC = 45
TOKEN_MAX_AGE = 7 * 24 * 3600


def confirm_token_from_request(request) -> str:
    auth = request.headers.get("Authorization") or ""
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return (request.headers.get("X-Participant-Token") or "").strip()


def _can_access_same_group(me: Participant, other: Participant) -> bool:
    if me.pk == other.pk:
        return True
    if me.group_id is not None and other.group_id is not None and me.group_id == other.group_id:
        return True
    return False


def _is_group_product_representative(p: Participant) -> bool:
    """단체 상품(행사·비전트립) 수정: 대표자만. group_id 없으면 개인 신청으로 간주."""
    if p.group_id is None:
        return True
    return p.group_id == p.pk


def _participant_confirm_response_data(p: Participant) -> dict:
    """단체원이면 상품 신청 필드는 대표자와 동일하게 표시(대표 선택 기준)."""
    data = ParticipantSerializer(p).data
    if _is_group_product_representative(p):
        return data
    try:
        rep = Participant.objects.get(pk=p.group_id)
    except Participant.DoesNotExist:
        return data
    rep_data = ParticipantSerializer(rep).data
    data["product_application"] = rep_data["product_application"]
    data["product_application_detail"] = rep_data["product_application_detail"]
    return data


def _product_application_update_from_request(request) -> dict | None:
    raw = request.data.get("product_application_update")
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    return None


def _sync_group_members_product_from_representative(representative: Participant, pa_update: dict) -> None:
    """대표자가 상품을 저장한 뒤, 동일 group_id 단체원의 ProductApplication에 동일 옵션을 반영(이메일만 각자)."""
    if not _is_group_product_representative(representative) or representative.group_id is None:
        return
    gid = representative.group_id
    others = (
        Participant.objects.filter(group_id=gid)
        .exclude(pk=representative.pk)
        .select_related("product_application")
    )
    base = dict(pa_update)
    for p in others:
        app = getattr(p, "product_application", None)
        if app is None:
            continue
        payload = {**base, "applicant_email": (p.email or "").strip()}
        update_product_application_from_payload(app, payload)


def normalize_phone(s: str) -> str:
    return "".join(c for c in (s or "") if c.isdigit())


def find_participant_by_phone(phone_input: str) -> Participant | None:
    """숫자만 일치하는 최근 참가자 1명 (뒤 4자리로 후보 축소)."""
    nd = normalize_phone(phone_input)
    if len(nd) < 10:
        return None
    tail = nd[-4:]
    qs = Participant.objects.filter(phone__icontains=tail).order_by("-created_at")[:80]
    for p in qs:
        if normalize_phone(p.phone) == nd:
            return p
    return None


def _sign_token(participant_id: int) -> str:
    signer = signing.TimestampSigner(salt=SIGN_SALT)
    return signer.sign(str(participant_id))


def _unsign_token(token: str) -> int:
    signer = signing.TimestampSigner(salt=SIGN_SALT)
    return int(signer.unsign(token, max_age=TOKEN_MAX_AGE))


def _participant_from_token(token: str) -> Participant:
    pid = _unsign_token(token)
    return Participant.objects.get(pk=pid)


class SendParticipantSmsView(B2nResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        nd = normalize_phone(phone)
        if len(nd) < 10:
            return Response(
                {"detail": "휴대폰 번호를 올바르게 입력해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant = find_participant_by_phone(phone)
        if participant is None:
            return Response(
                {"detail": "해당 번호로 접수된 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cooldown_key = f"{PHONE_SEND_COOLDOWN_PREFIX}{nd}"
        if cache.get(cooldown_key):
            return Response(
                {"detail": "잠시 후 다시 인증번호를 요청해 주세요."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # 100000–999999 (항상 숫자 6자리)
        code = f"{secrets.randbelow(900000) + 100000}"
        cache_key = f"{PHONE_OTP_PREFIX}{nd}"
        cache.set(cache_key, {"participant_id": participant.pk, "code": code}, OTP_TTL)
        cache.set(cooldown_key, 1, SEND_COOLDOWN_SEC)

        msg = f"[B2N2027] 인증번호는 [{code}] 입니다. (10분 이내 입력)"

        sender = get_default_sms_sender_number()
        api_key = (getattr(settings, "ALIGO_API_KEY", "") or "").strip()
        user_id = (getattr(settings, "ALIGO_USER_ID", "") or "").strip()

        if not sender or not api_key or not user_id:
            if settings.DEBUG:
                logger.warning(
                    "[SMS OTP] Aligo 미설정 — 개발용 코드 participant_id=%s phone=%s code=%s",
                    participant.pk,
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
                logger.error("[SMS OTP] 발송 실패: %s", send_result)
                return Response(
                    {
                        "detail": send_result.get("message") or "인증 문자 발송에 실패했습니다. 잠시 후 다시 시도해 주세요.",
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


def _mask_phone(nd: str) -> str:
    if len(nd) >= 11:
        return f"{nd[:3]}-****-{nd[-4:]}"
    if len(nd) >= 8:
        return f"{nd[:2]}***{nd[-4:]}"
    return "****"


class VerifyParticipantSmsView(B2nResponseMixin, APIView):
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

        cache_key = f"{PHONE_OTP_PREFIX}{nd}"
        data = cache.get(cache_key)
        if not data or data.get("code") != code:
            return Response(
                {"detail": "인증번호가 올바르지 않거나 만료되었습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant = Participant.objects.filter(pk=data["participant_id"]).first()
        if participant is None:
            return Response({"detail": "신청 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        cache.delete(cache_key)
        token = _sign_token(participant.pk)
        return Response(
            {
                "token": token,
                "participant": ParticipantSerializer(participant).data,
            }
        )


class PublicParticipantMeView(B2nResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = confirm_token_from_request(request)
        if not token:
            return Response({"detail": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            participant = _participant_from_token(token)
        except (signing.BadSignature, signing.SignatureExpired, ValueError, Participant.DoesNotExist):
            return Response({"detail": "세션이 만료되었거나 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(_participant_confirm_response_data(participant))

    def patch(self, request):
        token = confirm_token_from_request(request)
        if not token:
            return Response({"detail": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            participant = _participant_from_token(token)
        except (signing.BadSignature, signing.SignatureExpired, ValueError, Participant.DoesNotExist):
            return Response({"detail": "세션이 만료되었거나 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        if participant.status not in ("APPLYING", "REVIEWING"):
            return Response(
                {"detail": "현재 상태에서는 신청 내용을 수정할 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        pa_update = _product_application_update_from_request(request)
        if pa_update is not None and not _is_group_product_representative(participant):
            return Response(
                {"detail": "단체 상품 신청은 대표자(첫 등록자)만 수정할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = ParticipantCreateSerializer(participant, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        participant.refresh_from_db()

        if pa_update is not None and _is_group_product_representative(participant):
            _sync_group_members_product_from_representative(participant, pa_update)

        participant.refresh_from_db()
        return Response(_participant_confirm_response_data(participant))


class ConfirmGroupMembersView(B2nResponseMixin, APIView):
    """동일 group_id 참가자 목록 (group_id 없으면 본인만)."""

    permission_classes = [AllowAny]

    def get(self, request):
        token = confirm_token_from_request(request)
        if not token:
            return Response({"detail": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            me = _participant_from_token(token)
        except (signing.BadSignature, signing.SignatureExpired, ValueError, Participant.DoesNotExist):
            return Response({"detail": "세션이 만료되었거나 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        if me.group_id is None:
            qs = Participant.objects.filter(pk=me.pk)
        else:
            qs = Participant.objects.filter(group_id=me.group_id).order_by("id")

        members = []
        for p in qs:
            members.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "organization": p.organization or "",
                    "status": p.status,
                    "status_display": p.get_status_display(),
                    "phone": p.phone,
                }
            )
        return Response({"members": members, "group_id": me.group_id})


class ConfirmParticipantByIdView(B2nResponseMixin, APIView):
    """토큰 소유자와 같은 그룹인 참가자만 조회·수정."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        token = confirm_token_from_request(request)
        if not token:
            return Response({"detail": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            me = _participant_from_token(token)
        except (signing.BadSignature, signing.SignatureExpired, ValueError, Participant.DoesNotExist):
            return Response({"detail": "세션이 만료되었거나 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        other = get_object_or_404(Participant, pk=pk)
        if not _can_access_same_group(me, other):
            return Response({"detail": "접근할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return Response(_participant_confirm_response_data(other))

    def patch(self, request, pk):
        token = confirm_token_from_request(request)
        if not token:
            return Response({"detail": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            me = _participant_from_token(token)
        except (signing.BadSignature, signing.SignatureExpired, ValueError, Participant.DoesNotExist):
            return Response({"detail": "세션이 만료되었거나 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        other = get_object_or_404(Participant, pk=pk)
        if not _can_access_same_group(me, other):
            return Response({"detail": "접근할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        if other.status not in ("APPLYING", "REVIEWING"):
            return Response(
                {"detail": "현재 상태에서는 신청 내용을 수정할 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        pa_update = _product_application_update_from_request(request)
        if pa_update is not None and not _is_group_product_representative(other):
            return Response(
                {"detail": "단체 상품 신청은 대표자(첫 등록자)만 수정할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = ParticipantCreateSerializer(other, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        other.refresh_from_db()

        if pa_update is not None and _is_group_product_representative(other):
            _sync_group_members_product_from_representative(other, pa_update)

        other.refresh_from_db()
        return Response(_participant_confirm_response_data(other))
