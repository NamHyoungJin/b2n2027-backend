from django.urls import path

from .views import SponsorInquiryView

urlpatterns = [
    path('contact/sponsor-inquiry/', SponsorInquiryView.as_view(), name='sponsor-inquiry'),
]
