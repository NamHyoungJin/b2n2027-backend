from django.contrib import admin

from .models import HomepageDocInfo


@admin.register(HomepageDocInfo)
class HomepageDocInfoAdmin(admin.ModelAdmin):
    list_display = ("doc_type", "title", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("doc_type", "title")
