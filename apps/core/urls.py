from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    GeneralInquiryView,
    InquiryAdminAnswerView,
    InquiryAdminDetailView,
    InquiryAdminListView,
    SponsorInquiryView,
)
from .views_board_files import BoardFileUploadView
from .views_sponsors import PublicSponsorViewSet, SponsorAdminViewSet

admin_router = DefaultRouter()
admin_router.register(r"board/sponsors", SponsorAdminViewSet, basename="admin-sponsor")

public_router = DefaultRouter()
public_router.register(r"public/sponsors", PublicSponsorViewSet, basename="public-sponsor")

urlpatterns = [
    path("contact/sponsor-inquiry/", SponsorInquiryView.as_view(), name="sponsor-inquiry"),
    path("contact/inquiries/", GeneralInquiryView.as_view(), name="general-inquiry"),
    path("contact/admin/inquiries/", InquiryAdminListView.as_view(), name="admin-inquiry-list"),
    path("contact/admin/inquiries/<int:inquiry_id>/", InquiryAdminDetailView.as_view(), name="admin-inquiry-detail"),
    path("contact/admin/inquiries/<int:inquiry_id>/answer/", InquiryAdminAnswerView.as_view(), name="admin-inquiry-answer"),
    path("board/files/upload/", BoardFileUploadView.as_view(), name="board-file-upload"),
]

urlpatterns += admin_router.urls
urlpatterns += public_router.urls
