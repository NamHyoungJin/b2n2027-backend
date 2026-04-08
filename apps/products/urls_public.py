from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views_public import PublicProductApplicationViewSet, PublicProductViewSet

router = DefaultRouter()
router.register(r"", PublicProductViewSet, basename="public-product")

urlpatterns = [
    path(
        "applications/",
        PublicProductApplicationViewSet.as_view({"post": "create"}),
    ),
    path("", include(router.urls)),
]
