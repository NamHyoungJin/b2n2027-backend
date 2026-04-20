from django.urls import path

from .views_public import HomepageDocPublicDetailView, HomepageDocPublicListView

urlpatterns = [
    path("", HomepageDocPublicListView.as_view()),
    path("<str:doc_type>/", HomepageDocPublicDetailView.as_view()),
]
