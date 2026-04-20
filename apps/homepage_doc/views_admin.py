from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_accounts.authentication import AdminJWTAuthentication
from apps.core.mixins import B2nResponseMixin

from .constants import HOMEPAGE_DOC_TYPES, HOMEPAGE_DOC_TYPES_ORDERED, HOMEPAGE_DOC_LABELS
from .models import HomepageDocInfo
from .serializers import HomepageDocAdminUpdateSerializer, HomepageDocReadSerializer


class HomepageDocAdminListView(B2nResponseMixin, APIView):
    """4종 전체 — 게시 여부 무관."""

    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = HomepageDocInfo.objects.filter(doc_type__in=HOMEPAGE_DOC_TYPES)
        order = {dt: i for i, dt in enumerate(HOMEPAGE_DOC_TYPES_ORDERED)}
        rows = sorted(qs, key=lambda o: order.get(o.doc_type, 99))
        data = HomepageDocReadSerializer(rows, many=True).data
        return Response({"documents": data})


class HomepageDocAdminDetailPutView(B2nResponseMixin, APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, doc_type):
        if doc_type not in HOMEPAGE_DOC_TYPES:
            return Response({"detail": "지원하지 않는 doc_type 입니다."}, status=400)
        obj, _ = HomepageDocInfo.objects.get_or_create(
            doc_type=doc_type,
            defaults={
                "title": HOMEPAGE_DOC_LABELS.get(doc_type),
                "body_html": "",
                "is_published": False,
            },
        )
        ser = HomepageDocAdminUpdateSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        obj.refresh_from_db()
        return Response(HomepageDocReadSerializer(obj).data)
