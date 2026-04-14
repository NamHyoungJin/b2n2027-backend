# Generated manually for group_id

from django.db import migrations, models


def backfill_group_id(apps, schema_editor):
    Participant = apps.get_model("participants", "Participant")
    for p in Participant.objects.all().only("id", "uuid", "group_id"):
        if p.group_id is None:
            p.group_id = p.uuid
            p.save(update_fields=["group_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("participants", "0012_remove_participant_vision_trip_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="group_id",
            field=models.UUIDField(
                blank=True,
                db_index=True,
                help_text="단체 등록 시 대표(첫 참가자)의 uuid, 개인 등록 시 본인 uuid와 동일",
                null=True,
                verbose_name="그룹 ID",
            ),
        ),
        migrations.RunPython(backfill_group_id, migrations.RunPython.noop),
    ]
