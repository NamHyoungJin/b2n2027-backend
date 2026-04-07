from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.admin_accounts.authentication import AdminJWTAuthentication

from .models import BoardNotice
from .pagination import NoticePagination
from .serializers import (
    BoardNoticeDetailSerializer,
    BoardNoticeListSerializer,
    BoardNoticeWriteSerializer,
)


class NoticePublicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    공개 공지 — 인증 없이 목록·상세 조회.
    상세 조회 시 view_count +1
    """

    queryset = BoardNotice.objects.all()
    permission_classes = [AllowAny]
    pagination_class = NoticePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_pinned"]
    search_fields = ["title", "subtitle", "content"]
    ordering_fields = ["created_at", "view_count", "title", "id"]
    ordering = ["-is_pinned", "-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BoardNoticeDetailSerializer
        return BoardNoticeListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        BoardNotice.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NoticeAdminViewSet(viewsets.ModelViewSet):
    """관리자 공지 CRUD — Admin JWT 필수 (PlanDoc 권한 정책)."""

    queryset = BoardNotice.objects.all()
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = NoticePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_pinned"]
    search_fields = ["title", "subtitle", "content"]
    ordering_fields = ["created_at", "view_count", "title", "id"]
    ordering = ["-is_pinned", "-created_at"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BoardNoticeWriteSerializer
        if self.action == "retrieve":
            return BoardNoticeDetailSerializer
        return BoardNoticeListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        BoardNotice.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
