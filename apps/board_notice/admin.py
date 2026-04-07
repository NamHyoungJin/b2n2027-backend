from django.contrib import admin

from .models import BoardNotice


@admin.register(BoardNotice)
class BoardNoticeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subtitle", "is_pinned", "view_count", "created_at")
    list_filter = ("is_pinned",)
    search_fields = ("title", "subtitle", "content")
