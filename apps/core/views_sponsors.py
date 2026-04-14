from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.admin_accounts.authentication import AdminJWTAuthentication
from apps.core.mixins import B2nResponseMixin
from apps.core.models import Sponsor
from apps.core.s3_storage import delete_storage_key
from apps.core.serializers import SponsorAdminSerializer, SponsorPublicSerializer


class SponsorAdminViewSet(B2nResponseMixin, viewsets.ModelViewSet):
    queryset = Sponsor.objects.all().order_by("sort_order", "id")
    serializer_class = SponsorAdminSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name"]
    ordering_fields = ["sort_order", "created_at", "id", "name"]
    ordering = ["sort_order", "id"]
    pagination_class = None

    def perform_update(self, serializer):
        old = self.get_object()
        old_key = old.image_s3_key
        sponsor = serializer.save()
        if old_key and old_key != sponsor.image_s3_key:
            delete_storage_key(old_key)

    def perform_destroy(self, instance):
        image_key = instance.image_s3_key
        instance.delete()
        delete_storage_key(image_key)


class PublicSponsorViewSet(B2nResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = SponsorPublicSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    lookup_field = "pk"
    pagination_class = None

    def get_queryset(self):
        return Sponsor.objects.filter(is_active=True).order_by("sort_order", "id")
