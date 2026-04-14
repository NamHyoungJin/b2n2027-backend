from django.urls import path
from rest_framework.routers import DefaultRouter

from .public_confirmation import (
    ConfirmGroupMembersView,
    ConfirmParticipantByIdView,
    PublicParticipantMeView,
    SendParticipantSmsView,
    VerifyParticipantSmsView,
)
from .batch_register import RegisterBatchView
from .public_registration import SendRegistrationSmsView, VerifyRegistrationSmsView
from .views import ParticipantViewSet

router = DefaultRouter()
router.register(r'participants', ParticipantViewSet, basename='participant')

urlpatterns = [
    path('participants/register_batch/', RegisterBatchView.as_view()),
    path('participants/confirm/send-sms/', SendParticipantSmsView.as_view()),
    path('participants/confirm/verify/', VerifyParticipantSmsView.as_view()),
    path('participants/confirm/me/', PublicParticipantMeView.as_view()),
    path('participants/confirm/group_members/', ConfirmGroupMembersView.as_view()),
    path('participants/confirm/participants/<int:pk>/', ConfirmParticipantByIdView.as_view()),
    path('participants/register/send-sms/', SendRegistrationSmsView.as_view()),
    path('participants/register/verify/', VerifyRegistrationSmsView.as_view()),
] + router.urls
