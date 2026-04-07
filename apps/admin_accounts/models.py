import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models


def generate_admin_sid() -> str:
    return f"ADM{uuid.uuid4().hex[:12].upper()}"


class AdminMemberShip(models.Model):
    """B2N2027 관리자 페이지 전용 계정."""

    memberShipSid = models.CharField(
        primary_key=True,
        max_length=32,
        default=generate_admin_sid,
        editable=False,
        verbose_name="회원 SID",
    )
    memberShipId = models.CharField(max_length=50, unique=True, verbose_name="회원 ID")
    memberShipPassword = models.CharField(max_length=255, verbose_name="비밀번호")
    memberShipName = models.CharField(max_length=100, verbose_name="이름")
    memberShipEmail = models.EmailField(unique=True, verbose_name="이메일")
    memberShipPhone = models.CharField(max_length=20, blank=True, default="", verbose_name="전화번호")

    memberShipLevel = models.IntegerField(default=1, verbose_name="레벨")
    is_admin = models.BooleanField(default=False, verbose_name="설정관리 권한")
    is_active = models.BooleanField(default=True, verbose_name="활성")

    last_login = models.DateTimeField(blank=True, null=True, verbose_name="마지막 로그인")
    login_count = models.IntegerField(default=0, verbose_name="로그인 횟수")
    token_issued_at = models.DateTimeField(blank=True, null=True, verbose_name="마지막 토큰 발급")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        db_table = "adminMemberShip"
        verbose_name = "관리자 회원"
        verbose_name_plural = "관리자 회원"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["memberShipId"]),
            models.Index(fields=["memberShipEmail"]),
            models.Index(fields=["is_active", "is_admin"]),
        ]

    def __str__(self):
        return f"{self.memberShipName} ({self.memberShipId})"

    def set_password(self, raw_password: str):
        self.memberShipPassword = make_password(raw_password)
        self.save(update_fields=["memberShipPassword"])

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.memberShipPassword)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
