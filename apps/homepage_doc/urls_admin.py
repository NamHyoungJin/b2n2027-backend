from django.urls import path

from .views_admin import HomepageDocAdminDetailPutView, HomepageDocAdminListView

urlpatterns = [
    path("", HomepageDocAdminListView.as_view()),
    path("<str:doc_type>/", HomepageDocAdminDetailPutView.as_view()),
]
