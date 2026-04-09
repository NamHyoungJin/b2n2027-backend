from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.admin_accounts.authentication import AdminJWTAuthentication
from apps.core.mixins import B2nResponseMixin

from .lang_utils import notice_has_lang
from .models import BoardNotice
from .pagination import NoticePagination
from .serializers import (
    BoardNoticeAdminDetailSerializer,
    BoardNoticeAdminListSerializer,
    BoardNoticePublicDetailSerializer,
    BoardNoticePublicListSerializer,
    BoardNoticeWriteSerializer,
)


class NoticePublicViewSet(B2nResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    공개 공지 — 인증 없이 목록·상세 조회.
    `?lang=ko|en` (기본 ko): 해당 언어에 입력이 있는 공지만 목록에 포함, 응답 필드는 title·subtitle·content로 매핑.
    상세 조회 시 view_count +1
    """

    permission_classes = [AllowAny]
    pagination_class = NoticePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_pinned"]
    search_fields = [
        "title_ko",
        "title_en",
        "subtitle_ko",
        "subtitle_en",
        "content_ko",
        "content_en",
    ]
    ordering_fields = ["created_at", "view_count", "title_ko", "title_en", "id"]
    ordering = ["-is_pinned", "-created_at"]

    def get_queryset(self):
        qs = BoardNotice.objects.all()
        lang = self.request.query_params.get("lang", "ko")
        if lang not in ("ko", "en"):
            lang = "ko"
        if lang == "en":
            qs = qs.exclude(title_en="", subtitle_en="", content_en="")
        else:
            qs = qs.exclude(title_ko="", subtitle_ko="", content_ko="")
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BoardNoticePublicDetailSerializer
        return BoardNoticePublicListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        lang = self.request.query_params.get("lang", "ko")
        ctx["lang"] = lang if lang in ("ko", "en") else "ko"
        return ctx

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        lang = request.query_params.get("lang", "ko")
        if lang not in ("ko", "en"):
            lang = "ko"
        if not notice_has_lang(instance, lang):
            return Response(status=404)
        BoardNotice.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NoticeAdminViewSet(B2nResponseMixin, viewsets.ModelViewSet):
    """관리자 공지 CRUD — Admin JWT 필수 (PlanDoc 권한 정책). 한·영 필드 전체 노출."""

    queryset = BoardNotice.objects.all()
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = NoticePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_pinned"]
    search_fields = [
        "title_ko",
        "title_en",
        "subtitle_ko",
        "subtitle_en",
        "content_ko",
        "content_en",
    ]
    ordering_fields = ["created_at", "view_count", "title_ko", "title_en", "id"]
    ordering = ["-is_pinned", "-created_at"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BoardNoticeWriteSerializer
        if self.action == "retrieve":
            return BoardNoticeAdminDetailSerializer
        return BoardNoticeAdminListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        BoardNotice.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
