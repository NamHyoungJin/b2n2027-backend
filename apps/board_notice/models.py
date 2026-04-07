from django.db import models


class BoardNotice(models.Model):
    """공지사항 — 물리 테이블 `board_notice` (PlanDoc/board_notice.md)."""

    title = models.CharField(max_length=255, verbose_name="제목")
    subtitle = models.CharField(max_length=500, blank=True, default="", verbose_name="부제목")
    content = models.TextField(verbose_name="내용")
    is_pinned = models.BooleanField(default=False, verbose_name="상단 고정")
    view_count = models.IntegerField(default=0, verbose_name="조회수")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록일시")

    class Meta:
        db_table = "board_notice"
        ordering = ["-is_pinned", "-created_at"]
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"

    def __str__(self):
        return self.title
