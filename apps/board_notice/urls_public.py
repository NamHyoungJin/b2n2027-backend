from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NoticePublicViewSet

router = DefaultRouter()
router.register(r"", NoticePublicViewSet, basename="notice-public")

urlpatterns = [
    path("", include(router.urls)),
]
