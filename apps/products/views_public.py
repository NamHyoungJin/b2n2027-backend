"""공개(비로그인) 상품 조회·신청 — www 등록 폼용."""

from django.db.models import Prefetch
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core.mixins import B2nResponseMixin

from .models import Product, ProductApplication, ProductOptionItem
from .serializers import (
    ProductApplicationCreateSerializer,
    ProductApplicationReadSerializer,
    ProductRetrieveSerializer,
)


class PublicProductViewSet(B2nResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    GET /api/public/products/ — ACTIVE 상품 목록
    GET /api/public/products/{id}/ — 상세 (옵션은 is_active만 prefetch)
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ProductRetrieveSerializer
    lookup_field = "pk"

    def get_queryset(self):
        qs = (
            Product.objects.filter(status="ACTIVE")
            .prefetch_related(
                Prefetch(
                    "option_items",
                    queryset=ProductOptionItem.objects.filter(is_active=True).order_by(
                        "sort_order", "id"
                    ),
                ),
                "detail_images",
            )
            .order_by("-created_at")
        )
        return qs


class PublicProductApplicationViewSet(B2nResponseMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    POST /api/public/products/applications/ — 신청 생성 (서버 금액 검증 동일)
    """

    queryset = ProductApplication.objects.prefetch_related("option_lines").all()
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_serializer_class(self):
        return ProductApplicationCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = ProductApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        app = serializer.save()
        out = ProductApplicationReadSerializer(app, context={"request": request})
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)
