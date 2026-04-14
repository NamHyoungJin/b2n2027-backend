from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.admin_accounts.authentication import AdminJWTAuthentication
from apps.core.mixins import B2nResponseMixin

from .models import Product, ProductApplication, ProductDetailImage, ProductOptionItem
from .serializers import (
    ProductApplicationCreateSerializer,
    ProductApplicationReadSerializer,
    ProductListSerializer,
    ProductOptionItemSerializer,
    ProductRetrieveSerializer,
    ProductWriteSerializer,
)


class ProductAdminViewSet(B2nResponseMixin, viewsets.ModelViewSet):
    """관리자 상품 CRUD — Admin JWT 필수."""

    queryset = Product.objects.prefetch_related("detail_images", "option_items").all()
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "segment"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "base_price", "id"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ProductWriteSerializer
        return ProductRetrieveSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        self._save_detail_images(product, request)
        out = ProductRetrieveSerializer(product, context={"request": request})
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        self._maybe_replace_detail_images(product, request)
        out = ProductRetrieveSerializer(product, context={"request": request})
        return Response(out.data)

    def _save_detail_images(self, product, request):
        files = request.FILES.getlist("detail_images")
        for i, f in enumerate(files):
            ProductDetailImage.objects.create(product=product, image=f, sort_order=i)

    def _maybe_replace_detail_images(self, product, request):
        files = request.FILES.getlist("detail_images")
        raw_clear = request.data.get("clear_detail_images")
        clear = str(raw_clear).lower() in ("1", "true", "yes", "on")
        if files:
            product.detail_images.all().delete()
            for i, f in enumerate(files):
                ProductDetailImage.objects.create(product=product, image=f, sort_order=i)
        elif clear:
            product.detail_images.all().delete()


class ProductOptionItemAdminViewSet(B2nResponseMixin, viewsets.ModelViewSet):
    """상품별 비전트립 코스 옵션 CRUD — `/board/products/{product_pk}/option-items/`"""

    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProductOptionItemSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = None

    def get_queryset(self):
        return ProductOptionItem.objects.filter(product_id=self.kwargs["product_pk"])

    def perform_create(self, serializer):
        serializer.save(product_id=self.kwargs["product_pk"])


class ProductApplicationAdminViewSet(
    B2nResponseMixin, mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    상품 신청 생성·목록 — 서버 `total_amount` 재계산 (PlanDoc §19~23).
    `POST /api/board/products/applications/`
    """

    queryset = ProductApplication.objects.prefetch_related("option_lines").all()
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser]
    ordering = ["-created_at"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return ProductApplicationCreateSerializer
        return ProductApplicationReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = ProductApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        app = serializer.save()
        out = ProductApplicationReadSerializer(app, context={"request": request})
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)
