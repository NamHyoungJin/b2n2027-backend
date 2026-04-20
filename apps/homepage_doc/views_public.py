from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.mixins import B2nResponseMixin

from .constants import HOMEPAGE_DOC_TYPES, HOMEPAGE_DOC_TYPES_ORDERED
from .models import HomepageDocInfo
from .serializers import HomepageDocReadSerializer


class HomepageDocPublicListView(B2nResponseMixin, APIView):
    """게시된 문서만 목록."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        qs = HomepageDocInfo.objects.filter(is_published=True, doc_type__in=HOMEPAGE_DOC_TYPES)
        order = {dt: i for i, dt in enumerate(HOMEPAGE_DOC_TYPES_ORDERED)}
        rows = sorted(qs, key=lambda o: order.get(o.doc_type, 99))
        data = HomepageDocReadSerializer(rows, many=True).data
        return Response({"documents": data}, headers={"Cache-Control": "no-store, max-age=0"})


class HomepageDocPublicDetailView(B2nResponseMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, doc_type):
        if doc_type not in HOMEPAGE_DOC_TYPES:
            return Response(status=404)
        try:
            obj = HomepageDocInfo.objects.get(doc_type=doc_type)
        except HomepageDocInfo.DoesNotExist:
            return Response(status=404)
        if not obj.is_published:
            return Response(status=404)
        data = HomepageDocReadSerializer(obj).data
        return Response(data, headers={"Cache-Control": "no-store, max-age=0"})
