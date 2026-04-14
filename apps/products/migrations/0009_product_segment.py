# Product.segment — 구분(기본상품 / 추가상품)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0008_product_price_a_b"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="segment",
            field=models.CharField(
                choices=[("BASIC", "기본상품"), ("ADDITIONAL", "추가상품")],
                default="BASIC",
                max_length=20,
                verbose_name="구분",
            ),
        ),
    ]
