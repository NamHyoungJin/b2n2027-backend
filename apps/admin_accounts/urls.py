from django.urls import path

from apps.admin_accounts import views

urlpatterns = [
    path("login/", views.AdminLoginView.as_view(), name="admin_login"),
    path("login", views.AdminLoginView.as_view(), name="admin_login_ns"),
    path("tokenrefresh/", views.TokenRefreshView.as_view(), name="admin_token_refresh"),
    path("tokenrefresh", views.TokenRefreshView.as_view(), name="admin_token_refresh_ns"),
    path("logout/", views.AdminLogoutView.as_view(), name="admin_logout"),
    path("logout", views.AdminLogoutView.as_view(), name="admin_logout_ns"),
    path("list/", views.AdminListView.as_view(), name="admin_list"),
    path("list", views.AdminListView.as_view(), name="admin_list_ns"),
    path("join/", views.AdminRegisterView.as_view(), name="admin_join"),
    path("join", views.AdminRegisterView.as_view(), name="admin_join_ns"),
    path("update/", views.AdminUpdateView.as_view(), name="admin_update"),
    path("update", views.AdminUpdateView.as_view(), name="admin_update_ns"),
    path("deactivate/", views.AdminDeactivateView.as_view(), name="admin_deactivate"),
    path("deactivate", views.AdminDeactivateView.as_view(), name="admin_deactivate_ns"),
]
