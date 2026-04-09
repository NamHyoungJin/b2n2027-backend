# Generated manually — 한·영 필드 분리

from django.db import migrations, models


def copy_to_ko(apps, schema_editor):
    BoardNotice = apps.get_model("board_notice", "BoardNotice")
    for row in BoardNotice.objects.all():
        row.title_ko = getattr(row, "title", "") or ""
        row.subtitle_ko = getattr(row, "subtitle", "") or ""
        row.content_ko = getattr(row, "content", "") or ""
        row.save(update_fields=["title_ko", "subtitle_ko", "content_ko"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("board_notice", "0002_boardnotice_subtitle"),
    ]

    operations = [
        migrations.AddField(
            model_name="boardnotice",
            name="title_ko",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="제목(한글)"),
        ),
        migrations.AddField(
            model_name="boardnotice",
            name="title_en",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="제목(영문)"),
        ),
        migrations.AddField(
            model_name="boardnotice",
            name="subtitle_ko",
            field=models.CharField(blank=True, default="", max_length=500, verbose_name="부제목(한글)"),
        ),
        migrations.AddField(
            model_name="boardnotice",
            name="subtitle_en",
            field=models.CharField(blank=True, default="", max_length=500, verbose_name="부제목(영문)"),
        ),
        migrations.AddField(
            model_name="boardnotice",
            name="content_ko",
            field=models.TextField(blank=True, default="", verbose_name="내용(한글)"),
        ),
        migrations.AddField(
            model_name="boardnotice",
            name="content_en",
            field=models.TextField(blank=True, default="", verbose_name="내용(영문)"),
        ),
        migrations.RunPython(copy_to_ko, noop_reverse),
        migrations.RemoveField(model_name="boardnotice", name="title"),
        migrations.RemoveField(model_name="boardnotice", name="subtitle"),
        migrations.RemoveField(model_name="boardnotice", name="content"),
    ]
