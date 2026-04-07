"""최초 관리자 계정 생성 (운영/개발 시드)."""
import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from apps.admin_accounts.models import AdminMemberShip


class Command(BaseCommand):
    help = "B2N2027 기본 관리자(admin@b2n2027.org)를 생성/보정합니다."

    def add_arguments(self, parser):
        parser.add_argument("--id", default="admin@b2n2027.org", dest="member_id", help="로그인 ID")
        parser.add_argument(
            "--password",
            default=os.getenv("B2N_ADMIN_INIT_PASSWORD", "ChangeMe1234!"),
            help="초기 비밀번호 (운영에서는 반드시 변경)",
        )
        parser.add_argument("--name", default="시스템관리자", dest="name", help="이름")
        parser.add_argument("--email", default="admin@b2n2027.org", dest="email", help="이메일")

    def handle(self, *args, **options):
        mid = options["member_id"]
        email = options["email"]
        password = options["password"]
        name = options["name"]

        # 동일 이메일이 다른 ID에 묶여 있으면 안전하게 중단
        email_owner = AdminMemberShip.objects.filter(memberShipEmail=email).exclude(memberShipId=mid).first()
        if email_owner:
            self.stdout.write(
                self.style.ERROR(
                    f"이메일 {email} 은 이미 다른 계정({email_owner.memberShipId})에서 사용 중입니다."
                )
            )
            return

        admin, created = AdminMemberShip.objects.get_or_create(
            memberShipId=mid,
            defaults={
                "memberShipPassword": make_password(password),
                "memberShipName": name,
                "memberShipEmail": email,
                "memberShipPhone": "",
                "memberShipLevel": 99,
                "is_admin": True,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"관리자 생성 완료: {mid}"))
            self.stdout.write("초기 비밀번호로 로그인 후 반드시 변경하세요.")
            return

        changed = False
        if admin.memberShipEmail != email:
            admin.memberShipEmail = email
            changed = True
        if admin.memberShipName != name:
            admin.memberShipName = name
            changed = True
        if admin.memberShipLevel < 99:
            admin.memberShipLevel = 99
            changed = True
        if not admin.is_admin:
            admin.is_admin = True
            changed = True
        if not admin.is_active:
            admin.is_active = True
            changed = True

        if changed:
            admin.save(update_fields=["memberShipEmail", "memberShipName", "memberShipLevel", "is_admin", "is_active", "updated_at"])
            self.stdout.write(self.style.SUCCESS(f"기존 계정을 관리자 권한으로 보정했습니다: {mid}"))
        else:
            self.stdout.write(self.style.WARNING(f"이미 관리자 계정이 준비되어 있습니다: {mid}"))
