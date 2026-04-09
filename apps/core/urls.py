from django.urls import path

from .views import SponsorInquiryView
from .views_board_files import BoardFileUploadView

urlpatterns = [
    path("contact/sponsor-inquiry/", SponsorInquiryView.as_view(), name="sponsor-inquiry"),
    path("board/files/upload/", BoardFileUploadView.as_view(), name="board-file-upload"),
]
