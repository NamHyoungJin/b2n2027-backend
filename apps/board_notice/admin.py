from django.contrib import admin

from .models import BoardNotice


@admin.register(BoardNotice)
class BoardNoticeAdmin(admin.ModelAdmin):
    list_display = ("id", "title_ko", "title_en", "is_pinned", "view_count", "created_at")
    list_filter = ("is_pinned",)
    search_fields = (
        "title_ko",
        "title_en",
        "subtitle_ko",
        "subtitle_en",
        "content_ko",
        "content_en",
    )
