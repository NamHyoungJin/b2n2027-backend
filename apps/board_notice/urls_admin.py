from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NoticeAdminViewSet

router = DefaultRouter()
router.register(r"", NoticeAdminViewSet, basename="notice-admin")

urlpatterns = [
    path("", include(router.urls)),
]
