from django.urls import path

from .views import (
    GeneralInquiryView,
    InquiryAdminAnswerView,
    InquiryAdminDetailView,
    InquiryAdminListView,
    SponsorInquiryView,
)
from .views_board_files import BoardFileUploadView

urlpatterns = [
    path("contact/sponsor-inquiry/", SponsorInquiryView.as_view(), name="sponsor-inquiry"),
    path("contact/inquiries/", GeneralInquiryView.as_view(), name="general-inquiry"),
    path("contact/admin/inquiries/", InquiryAdminListView.as_view(), name="admin-inquiry-list"),
    path("contact/admin/inquiries/<int:inquiry_id>/", InquiryAdminDetailView.as_view(), name="admin-inquiry-detail"),
    path("contact/admin/inquiries/<int:inquiry_id>/answer/", InquiryAdminAnswerView.as_view(), name="admin-inquiry-answer"),
    path("board/files/upload/", BoardFileUploadView.as_view(), name="board-file-upload"),
]
