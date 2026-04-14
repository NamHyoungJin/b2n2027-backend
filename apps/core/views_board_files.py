"""관리자 전용 파일 업로드 — POST /api/board/files/upload/ (PlanDoc/s3Rules.md)."""

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_accounts.authentication import AdminJWTAuthentication
from apps.core.mixins import B2nResponseMixin
from apps.core.s3_storage import (
    image_url_for_key,
    is_s3_configured,
    upload_product_option_file,
    upload_sponsor_file,
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class BoardFileUploadView(B2nResponseMixin, APIView):
    """
    multipart `file` 한 개.
    purpose=product_option (기본) — 상품 옵션 이미지용 키 접두사 `product-option-items/`.
    응답: { "key": str, "url": str } — url은 미리보기용(Presigned 또는 로컬 MEDIA URL).
    """

    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        f = request.FILES.get("file")
        if not f:
            return Response({"file": ["파일이 필요합니다."]}, status=status.HTTP_400_BAD_REQUEST)
        if f.size > MAX_UPLOAD_BYTES:
            return Response({"file": ["파일 크기는 5MB 이하여야 합니다."]}, status=status.HTTP_400_BAD_REQUEST)

        purpose = (request.data.get("purpose") or "product_option").strip()
        if purpose not in {"product_option", "sponsor"}:
            return Response({"purpose": ["지원하지 않는 purpose입니다."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if purpose == "sponsor":
                key = upload_sponsor_file(f)
            else:
                key = upload_product_option_file(f)
        except ValueError as e:
            return Response({"file": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": ["업로드에 실패했습니다."]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        url = image_url_for_key(key, request)
        return Response({"key": key, "url": url, "storage": "s3" if is_s3_configured() else "local"}, status=status.HTTP_201_CREATED)
