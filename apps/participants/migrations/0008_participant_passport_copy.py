# Generated manually — apply with: python manage.py migrate

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("participants", "0007_participant_attendee_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="passport_copy",
            field=models.ImageField(
                blank=True,
                db_comment="여권 사본 이미지 경로",
                help_text="개인 등록 시 여권 사본 이미지(서버 저장, 공개 URL 미제공)",
                null=True,
                upload_to="passport_copies/",
                verbose_name="여권 사본",
            ),
        ),
    ]
