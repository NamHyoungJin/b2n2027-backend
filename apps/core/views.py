import logging
from html import escape

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_accounts.authentication import AdminJWTAuthentication
from apps.core.mail import send_email
from apps.core.mixins import B2nResponseMixin
from apps.core.models import Inquiry

from .serializers import (
    GeneralInquirySerializer,
    InquiryAnswerSerializer,
    InquiryDetailSerializer,
    InquiryListSerializer,
    SponsorInquirySerializer,
)

logger = logging.getLogger(__name__)


def _text_to_html(text: str) -> str:
    return (
        '<div style="white-space:pre-wrap;font-family:Arial,sans-serif;'
        'font-size:14px;line-height:1.6;">'
        f"{escape(text)}"
        "</div>"
    )


def _send_inquiry_notification_email(inquiry: Inquiry) -> None:
    body_lines = [
        f'[B2N Turkish Nights 2027] {inquiry.get_type_display()}가 접수되었습니다.',
        '',
        f'유형: {inquiry.get_type_display()}',
        f'이름: {inquiry.name}',
        f'이메일: {inquiry.email}',
        f'제목: {inquiry.subject}',
        f'회사/단체명: {inquiry.company_name or "(미입력)"}',
        f'연락처: {inquiry.phone or "(미입력)"}',
        '',
        '문의 내용:',
        inquiry.message or '(내용 없음)',
        '',
    ]
    body = '\n'.join(body_lines)
    attachments: list[tuple[str, bytes, str | None]] = []

    to_addr = getattr(settings, 'SPONSOR_INQUIRY_TO', None) or settings.DEFAULT_FROM_EMAIL
    if inquiry.logo:
        inquiry.logo.open("rb")
        try:
            attachments.append(
                (
                    inquiry.logo.name.rsplit("/", 1)[-1],
                    inquiry.logo.read(),
                    getattr(inquiry.logo.file, "content_type", None) or "application/octet-stream",
                )
            )
        finally:
            inquiry.logo.close()
    ok = send_email(
        to_addr,
        f'[B2N2027 {inquiry.get_type_display()}] {inquiry.subject}',
        _text_to_html(body),
        body_text=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        reply_to=inquiry.email,
        attachments=attachments,
    )
    if not ok:
        raise RuntimeError("gmail helper send failed")


def _create_inquiry(
    *,
    inquiry_type: str,
    validated: dict,
) -> Inquiry:
    if inquiry_type == Inquiry.TYPE_SPONSOR:
        name = validated['name']
        company = validated.get('company_name') or ''
        subject = company or f'{name}님의 협찬 문의'
    else:
        subject = validated['subject']

    return Inquiry.objects.create(
        type=inquiry_type,
        name=validated['name'],
        email=validated['email'],
        subject=subject,
        company_name=validated.get('company_name', ''),
        phone=validated.get('phone', ''),
        message=validated.get('message', ''),
        logo=validated.get('logo'),
    )


class SponsorInquiryView(B2nResponseMixin, APIView):
    """
    협찬 문의: multipart 폼으로 접수 후 수신 메일함으로 전송.
    첨부 `logo`는 협찬사 로고 이미지(선택).
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = SponsorInquirySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        inquiry = _create_inquiry(
            inquiry_type=Inquiry.TYPE_SPONSOR,
            validated=serializer.validated_data,
        )

        try:
            _send_inquiry_notification_email(inquiry)
        except Exception as e:
            logger.exception('sponsor_inquiry email failed: %s', e)
            return Response(
                {'detail': '메일 전송에 실패했습니다. 잠시 후 다시 시도하거나 이메일로 직접 문의해 주세요.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({'ok': True}, status=status.HTTP_200_OK)


class GeneralInquiryView(B2nResponseMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        serializer = GeneralInquirySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        inquiry = _create_inquiry(
            inquiry_type=Inquiry.TYPE_GENERAL,
            validated=serializer.validated_data,
        )

        try:
            _send_inquiry_notification_email(inquiry)
        except Exception as e:
            logger.exception('general_inquiry email failed: %s', e)
            return Response(
                {'detail': '문의 접수 메일 전송에 실패했습니다. 잠시 후 다시 시도해 주세요.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({'ok': True}, status=status.HTTP_200_OK)


class InquiryAdminListView(B2nResponseMixin, APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Inquiry.objects.select_related("answered_by").all()

        inquiry_type = (request.query_params.get("type") or "").strip().upper()
        if inquiry_type in {Inquiry.TYPE_GENERAL, Inquiry.TYPE_SPONSOR}:
            qs = qs.filter(type=inquiry_type)

        status_value = (request.query_params.get("status") or "").strip().lower()
        if status_value in {Inquiry.STATUS_PENDING, Inquiry.STATUS_ANSWERED}:
            qs = qs.filter(status=status_value)

        search = (request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(subject__icontains=search)
                | Q(message__icontains=search)
                | Q(company_name__icontains=search)
            )

        serializer = InquiryListSerializer(qs.order_by("-created_at"), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InquiryAdminDetailView(B2nResponseMixin, APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, inquiry_id: int):
        try:
            inquiry = Inquiry.objects.select_related("answered_by").get(pk=inquiry_id)
        except Inquiry.DoesNotExist:
            return Response({"detail": "문의를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = InquiryDetailSerializer(inquiry, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class InquiryAdminAnswerView(B2nResponseMixin, APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, inquiry_id: int):
        serializer = InquiryAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            inquiry = Inquiry.objects.select_related("answered_by").get(pk=inquiry_id)
        except Inquiry.DoesNotExist:
            return Response({"detail": "문의를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        answer = serializer.validated_data["answer"]
        subject = f"[B2N2027 문의답변] {inquiry.subject}"
        body = (
            f"{inquiry.name}님,\n\n"
            "문의해 주셔서 감사합니다. 아래와 같이 답변드립니다.\n\n"
            f"문의 제목: {inquiry.subject}\n"
            f"문의 내용: {inquiry.message or '(내용 없음)'}\n\n"
            "답변 내용:\n"
            f"{answer}\n"
        )

        ok = send_email(
            inquiry.email,
            subject,
            _text_to_html(body),
            body_text=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            reply_to=settings.DEFAULT_FROM_EMAIL,
        )
        if not ok:
            logger.error("inquiry answer email failed: gmail helper returned false")
            return Response(
                {"detail": "답변 메일 발송에 실패했습니다. 메일 설정을 확인해 주세요."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        inquiry.answer = answer
        inquiry.status = Inquiry.STATUS_ANSWERED
        inquiry.answered_at = timezone.now()
        inquiry.answered_by = request.user
        inquiry.save(update_fields=["answer", "status", "answered_at", "answered_by", "updated_at"])

        result = InquiryDetailSerializer(inquiry, context={"request": request}).data
        return Response(result, status=status.HTTP_200_OK)
