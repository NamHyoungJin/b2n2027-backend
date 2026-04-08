from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProductAdminViewSet, ProductApplicationAdminViewSet, ProductOptionItemAdminViewSet

router = DefaultRouter()
router.register(r"", ProductAdminViewSet, basename="product-admin")

urlpatterns = [
    path(
        "<int:product_pk>/option-items/",
        ProductOptionItemAdminViewSet.as_view({"get": "list", "post": "create"}),
    ),
    path(
        "<int:product_pk>/option-items/<int:pk>/",
        ProductOptionItemAdminViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "applications/",
        ProductApplicationAdminViewSet.as_view({"get": "list", "post": "create"}),
    ),
    path("", include(router.urls)),
]
