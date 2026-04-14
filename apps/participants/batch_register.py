"""
www `/apply` — 참가자·상품신청 다건을 하나의 DB 트랜잭션으로 처리 (부분 성공 없음).
"""

from __future__ import annotations

import base64
import logging

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.mixins import B2nResponseMixin
from apps.products.serializers import ProductApplicationCreateSerializer

from .models import Participant
from .public_registration import verify_registration_phone_token
from .serializers import MAX_PASSPORT_COPY_BYTES, ParticipantCreateSerializer, ParticipantSerializer

logger = logging.getLogger(__name__)

MAX_BATCH = 30


def _require_public_phone(participant_serializer: ParticipantCreateSerializer) -> None:
    """비관리자 등록 시 휴대폰 인증 — `ParticipantViewSet.create` 와 동일."""
    vd = participant_serializer.validated_data
    skip_verify = vd.get("group_member_without_phone_verification") is True
    token = (vd.get("phone_verification_token") or "").strip()
    phone = vd.get("phone", "")
    if skip_verify:
        org = (vd.get("organization") or "").strip()
        if not org:
            raise serializers.ValidationError(
                "단체 추가 참가자는 소속(단체명)이 입력된 경우에만 "
                "문자 인증 없이 등록할 수 있습니다."
            )
    elif not verify_registration_phone_token(token, phone):
        raise PermissionDenied(
            "휴대폰 인증이 필요합니다. 연락처 인증을 완료한 뒤 다시 시도해 주세요."
        )


class RegisterBatchView(B2nResponseMixin, APIView):
    """
    POST /api/participants/register_batch/

    - `application_template`: `ProductApplicationCreateSerializer` 공통 필드
      (각 행에서 `applicant_email` 만 참가자 이메일로 설정)
    - `participants`: 참가자 본문 배열 (`product_application_id`, `anchor_group_id` 는 서버가 설정)
    - `passport_copy`: 선택 — `{ "participant_index": 0, "filename": "x.jpg", "content_base64": "..." }`
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        body = request.data
        if not isinstance(body, dict):
            return Response({"detail": "JSON 객체가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        application_template = body.get("application_template")
        participants_in = body.get("participants")
        passport_meta = body.get("passport_copy")

        if not isinstance(application_template, dict):
            return Response(
                {"detail": "application_template 이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(participants_in, list) or len(participants_in) < 1:
            return Response(
                {"detail": "participants 배열이 1건 이상 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(participants_in) > MAX_BATCH:
            return Response(
                {"detail": f"한 번에 최대 {MAX_BATCH}명까지 등록할 수 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        passport_index: int | None = None
        passport_bytes: bytes | None = None
        passport_filename = "passport.jpg"

        if passport_meta:
            if not isinstance(passport_meta, dict):
                return Response({"detail": "passport_copy 형식이 올바르지 않습니다."}, status=400)
            try:
                passport_index = int(passport_meta.get("participant_index", -1))
            except (TypeError, ValueError):
                return Response({"detail": "passport_copy.participant_index 가 필요합니다."}, status=400)
            if passport_index < 0 or passport_index >= len(participants_in):
                return Response(
                    {"detail": "passport_copy.participant_index 가 범위를 벗어났습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            passport_filename = (passport_meta.get("filename") or "passport.jpg").strip() or "passport.jpg"
            b64 = passport_meta.get("content_base64")
            if not isinstance(b64, str) or not b64.strip():
                return Response({"detail": "passport_copy.content_base64 가 필요합니다."}, status=400)
            try:
                passport_bytes = base64.b64decode(b64, validate=True)
            except Exception:
                return Response({"detail": "passport_copy Base64 디코딩에 실패했습니다."}, status=400)
            if len(passport_bytes) > MAX_PASSPORT_COPY_BYTES:
                return Response(
                    {"detail": "여권 사본은 5MB 이하 이미지만 업로드할 수 있습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user = getattr(request, "user", None)
        is_admin = bool(
            user is not None
            and getattr(user, "is_authenticated", False)
            and not getattr(user, "is_anonymous", True)
        )

        created_payloads: list[dict] = []

        try:
            with transaction.atomic():
                anchor_pk: int | None = None

                for idx, row in enumerate(participants_in):
                    if not isinstance(row, dict):
                        raise serializers.ValidationError(f"participants[{idx}] 가 객체가 아닙니다.")

                    row = {k: v for k, v in row.items() if k not in ("product_application_id", "anchor_group_id")}

                    pa_payload = {**application_template, "applicant_email": (row.get("email") or "").strip()}
                    pa_ser = ProductApplicationCreateSerializer(data=pa_payload)
                    pa_ser.is_valid(raise_exception=True)
                    app = pa_ser.save()

                    pdata = {**row, "product_application_id": app.id}
                    if anchor_pk is not None:
                        pdata["anchor_group_id"] = anchor_pk

                    if passport_bytes is not None and passport_index == idx:
                        pdata["passport_copy"] = ContentFile(passport_bytes, name=passport_filename)

                    p_ser = ParticipantCreateSerializer(data=pdata)
                    p_ser.is_valid(raise_exception=True)

                    if not is_admin:
                        _require_public_phone(p_ser)

                    p_ser.save()

                    inst = Participant.objects.get(pk=p_ser.instance.pk)
                    created_payloads.append(ParticipantSerializer(inst).data)

                    if anchor_pk is None:
                        anchor_pk = inst.pk

        except APIException as e:
            detail = e.detail
            if isinstance(detail, dict):
                body = detail
            elif isinstance(detail, list):
                body = {"detail": detail}
            else:
                body = {"detail": str(detail)}
            return Response(body, status=e.status_code)
        except Exception as e:
            logger.exception("register_batch failed: %s", e)
            return Response(
                {"detail": "등록 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"participants": created_payloads, "count": len(created_payloads)},
            status=status.HTTP_201_CREATED,
        )
