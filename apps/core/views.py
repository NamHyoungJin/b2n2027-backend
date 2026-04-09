import logging

from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.mixins import B2nResponseMixin

from .serializers import SponsorInquirySerializer

logger = logging.getLogger(__name__)


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

        v = serializer.validated_data
        name = v['name']
        email = v['email']
        company = v.get('company_name') or ''
        phone = v.get('phone') or ''
        message = v.get('message') or ''
        logo = v.get('logo')

        body_lines = [
            '[B2N Turkish Nights 2027] 협찬 문의가 접수되었습니다.',
            '',
            f'이름: {name}',
            f'이메일: {email}',
            f'회사/단체명: {company or "(미입력)"}',
            f'연락처: {phone or "(미입력)"}',
            '',
            '문의 내용:',
            message or '(내용 없음)',
            '',
        ]
        body = '\n'.join(body_lines)

        to_addr = getattr(settings, 'SPONSOR_INQUIRY_TO', None) or settings.DEFAULT_FROM_EMAIL
        from_addr = settings.DEFAULT_FROM_EMAIL

        try:
            msg = EmailMessage(
                subject=f'[B2N2027 협찬문의] {name}',
                body=body,
                from_email=from_addr,
                to=[to_addr],
                reply_to=[email],
            )
            if logo is not None:
                raw = logo.read()
                msg.attach(
                    logo.name,
                    raw,
                    getattr(logo, 'content_type', None) or 'application/octet-stream',
                )
            msg.send(fail_silently=False)
        except Exception as e:
            logger.exception('sponsor_inquiry email failed: %s', e)
            return Response(
                {'detail': '메일 전송에 실패했습니다. 잠시 후 다시 시도하거나 이메일로 직접 문의해 주세요.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({'ok': True}, status=status.HTTP_200_OK)
