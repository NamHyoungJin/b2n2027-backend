# ProductApplication.additional_product / additional_tier

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0009_product_segment"),
    ]

    operations = [
        migrations.AddField(
            model_name="productapplication",
            name="additional_product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="additional_fee_applications",
                to="products.product",
                verbose_name="추가 상품(선택)",
            ),
        ),
        migrations.AddField(
            model_name="productapplication",
            name="additional_tier",
            field=models.CharField(
                choices=[
                    ("NONE", "NONE"),
                    ("ONE_NIGHT_TWO_DAYS", "ONE_NIGHT_TWO_DAYS"),
                    ("SAME_DAY", "SAME_DAY"),
                ],
                default="NONE",
                max_length=30,
                verbose_name="추가 상품 요금 구간",
            ),
        ),
    ]
