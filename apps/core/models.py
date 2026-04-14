from django.db import models


class Inquiry(models.Model):
    TYPE_SPONSOR = "SPONSOR"
    TYPE_GENERAL = "GENERAL"
    TYPE_CHOICES = [
        (TYPE_SPONSOR, "협찬 문의"),
        (TYPE_GENERAL, "일반 문의"),
    ]

    STATUS_PENDING = "pending"
    STATUS_ANSWERED = "answered"
    STATUS_CHOICES = [
        (STATUS_PENDING, "답변 대기"),
        (STATUS_ANSWERED, "답변 완료"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField(blank=True, default="")

    company_name = models.CharField(max_length=200, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    logo = models.ImageField(upload_to="inquiries/logos/", blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    answer = models.TextField(blank=True, default="")
    answered_at = models.DateTimeField(blank=True, null=True)
    answered_by = models.ForeignKey(
        "admin_accounts.AdminMemberShip",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="answered_inquiries",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inquiry"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["type", "status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"[{self.type}] {self.subject} <{self.email}>"
