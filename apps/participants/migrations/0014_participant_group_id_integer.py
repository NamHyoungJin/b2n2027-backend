# group_id: UUID -> participants.id (정수)

from django.db import migrations, models


def uuid_group_to_int(apps, schema_editor):
    Participant = apps.get_model("participants", "Participant")
    for p in Participant.objects.all():
        legacy_uuid = p.group_id
        if legacy_uuid is None:
            p.group_anchor_pk = p.id
        else:
            anchor = Participant.objects.filter(uuid=legacy_uuid).first()
            p.group_anchor_pk = anchor.id if anchor else p.id
        p.save(update_fields=["group_anchor_pk"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("participants", "0013_participant_group_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="group_anchor_pk",
            field=models.PositiveIntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="그룹 ID (전환용)",
            ),
        ),
        migrations.RunPython(uuid_group_to_int, noop),
        migrations.RemoveField(
            model_name="participant",
            name="group_id",
        ),
        migrations.RenameField(
            model_name="participant",
            old_name="group_anchor_pk",
            new_name="group_id",
        ),
        migrations.AlterField(
            model_name="participant",
            name="group_id",
            field=models.PositiveIntegerField(
                blank=True,
                db_index=True,
                help_text="단체 등록 시 대표(첫 참가자)의 participants.id, 개인 등록 시 본인 id",
                null=True,
                verbose_name="그룹 ID",
            ),
        ),
    ]
