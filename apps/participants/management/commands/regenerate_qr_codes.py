"""
프로덕션에서 QR 코드 파일이 없을 때(DB만 복사된 경우 등) 일괄 재생성.

사용 예:
  python manage.py regenerate_qr_codes           # path 있지만 파일 없는 참여자만 재생성
  python manage.py regenerate_qr_codes --all    # PAID 참여자 전부 재생성
"""
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.participants.models import Participant


class Command(BaseCommand):
    help = "QR 코드 이미지가 없는 참여자에 대해 QR을 (재)생성합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="path 유무와 관계없이 status=PAID인 참여자 전부 재생성",
        )

    def handle(self, *args, **options):
        if options["all"]:
            qs = Participant.objects.filter(status="PAID")
            self.stdout.write(f"PAID 참여자 전부 재생성: {qs.count()}명")
        else:
            # qr_image 필드에 path는 있지만 실제 파일이 없는 참여자
            media_root = getattr(settings, "MEDIA_ROOT", None)
            if not media_root:
                self.stderr.write("MEDIA_ROOT가 설정되지 않았습니다.")
                return
            to_regenerate = []
            for p in Participant.objects.filter(status="PAID").exclude(qr_image=""):
                path = p.qr_image.path if p.qr_image else None
                if path and not os.path.isfile(path):
                    to_regenerate.append(p)
            qs = to_regenerate
            self.stdout.write(f"파일이 없어 재생성할 참여자: {len(qs)}명 (MEDIA_ROOT={media_root})")

        for p in qs:
            try:
                p.generate_qr_code()
                p.save(update_fields=["qr_image", "updated_at"])
                self.stdout.write(self.style.SUCCESS(f"  participant_id={p.pk} uuid={p.uuid} ok"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  participant_id={p.pk} uuid={p.uuid} failed: {e}"))
