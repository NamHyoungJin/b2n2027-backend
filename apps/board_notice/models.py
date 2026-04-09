from django.db import models


class BoardNotice(models.Model):
    """공지사항 — 물리 테이블 `board_notice` (PlanDoc/board_notice.md). 한·영 필드 분리."""

    title_ko = models.CharField(max_length=255, default="", blank=True, verbose_name="제목(한글)")
    title_en = models.CharField(max_length=255, default="", blank=True, verbose_name="제목(영문)")
    subtitle_ko = models.CharField(max_length=500, default="", blank=True, verbose_name="부제목(한글)")
    subtitle_en = models.CharField(max_length=500, default="", blank=True, verbose_name="부제목(영문)")
    content_ko = models.TextField(default="", blank=True, verbose_name="내용(한글)")
    content_en = models.TextField(default="", blank=True, verbose_name="내용(영문)")
    is_pinned = models.BooleanField(default=False, verbose_name="상단 고정")
    view_count = models.IntegerField(default=0, verbose_name="조회수")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록일시")

    class Meta:
        db_table = "board_notice"
        ordering = ["-is_pinned", "-created_at"]
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"

    def __str__(self):
        return (self.title_ko or self.title_en or "").strip() or f"Notice #{self.pk}"
