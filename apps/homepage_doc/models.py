from django.db import models


class HomepageDocInfo(models.Model):
    """
    홈페이지 정책·약관 HTML — InDe `HomepageDocInfo`와 동일 역할.
    `doc_type` 당 1행 (UNIQUE), 총 4행 고정 시드.
    """

    doc_type = models.CharField(max_length=48, unique=True, db_index=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    body_html = models.TextField(default="", blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "homepage_doc_info"
        ordering = ["doc_type"]

    def __str__(self) -> str:
        return self.doc_type
