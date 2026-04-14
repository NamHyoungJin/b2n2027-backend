# 신규 상태 체계(신청중·신청확인중·…) 반영. 구 CANCEL_REQ 는 취소로 이관.

from django.db import migrations, models


def forwards_migrate_legacy_status(apps, schema_editor):
    Participant = apps.get_model("participants", "Participant")
    Participant.objects.filter(status="CANCEL_REQ").update(status="CANCELLED")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("participants", "0010_widen_participant_uuid_column"),
    ]

    operations = [
        migrations.RunPython(forwards_migrate_legacy_status, noop_reverse),
        migrations.AlterField(
            model_name="participant",
            name="status",
            field=models.CharField(
                choices=[
                    ("APPLYING", "신청중"),
                    ("REVIEWING", "신청확인중"),
                    ("PENDING", "입금대기"),
                    ("DEPOSIT_CONFIRMED", "입금확인"),
                    ("PAID", "신청완료"),
                    ("CANCELLED", "취소"),
                    ("REFUNDED", "환불"),
                ],
                db_comment="신청 처리 상태 (APPLYING, REVIEWING, PENDING, DEPOSIT_CONFIRMED, PAID, CANCELLED, REFUNDED)",
                default="APPLYING",
                help_text="신청중→신청확인중→입금대기→입금확인→신청완료 등 처리 단계",
                max_length=20,
                verbose_name="상태",
            ),
        ),
    ]
