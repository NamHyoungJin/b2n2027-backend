from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_remove_product_legacy_vision_opt_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="productoptionitem",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="products/option_items/",
                verbose_name="비전트립 카드 이미지",
            ),
        ),
        migrations.AddField(
            model_name="productoptionitem",
            name="audience",
            field=models.CharField(
                choices=[("GLOBAL", "GLOBAL"), ("KOREA", "KOREA")],
                default="GLOBAL",
                max_length=10,
                verbose_name="표시 구분",
            ),
        ),
        migrations.AddField(
            model_name="productoptionitem",
            name="choice_tier",
            field=models.CharField(
                choices=[("FIRST", "FIRST"), ("SECOND", "SECOND"), ("THIRD", "THIRD")],
                default="FIRST",
                max_length=10,
                verbose_name="선택 구분(지망)",
            ),
        ),
    ]
