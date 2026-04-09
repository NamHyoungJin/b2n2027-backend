# Generated manually for detail_content field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0006_productoptionitem_image_s3_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="productoptionitem",
            name="detail_content",
            field=models.TextField(
                blank=True,
                default="",
                help_text="TipTap HTML — 공지 본문과 동일 에디터(PlanDoc/board_notice.md).",
                verbose_name="상세 내용",
            ),
        ),
        migrations.AlterField(
            model_name="productoptionitem",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="짧은 안내·한 줄 요약(plain text 권장).",
                verbose_name="기본 내용",
            ),
        ),
        migrations.AlterField(
            model_name="productoptionitem",
            name="name",
            field=models.CharField(max_length=200, verbose_name="비전트립 제목"),
        ),
    ]
