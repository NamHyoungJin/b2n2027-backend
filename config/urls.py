"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls')),
    path('api/', include('apps.participants.urls')),
    path('api/adminMember/', include('apps.admin_accounts.urls')),
    path('api/notices/', include('apps.board_notice.urls_public')),
    path('api/board/notices/', include('apps.board_notice.urls_admin')),
    path('api/board/products/', include('apps.products.urls_admin')),
    path('api/public/products/', include('apps.products.urls_public')),
    path('api/messages/', include('apps.messages.urls')),
]

# MEDIA_ROOT 로 저장된 파일(/media/...) — DEBUG=False 일 때만 조건부로 붙이면 로컬에서 파일이 있어도 404가 난다.
# 운영은 보통 nginx 가 /media/ 를 직접 서빙하고, 그 앞단에서 막히면 Django 까지 오지 않는다.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
