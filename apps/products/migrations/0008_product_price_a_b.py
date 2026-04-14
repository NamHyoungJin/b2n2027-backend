# Generated manually for price_a_1n2d / price_b_day

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0007_productoptionitem_detail_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="price_a_1n2d",
            field=models.DecimalField(
                decimal_places=0,
                default=0,
                max_digits=12,
                verbose_name="가격 A (1박2일)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="price_b_day",
            field=models.DecimalField(
                decimal_places=0,
                default=0,
                max_digits=12,
                verbose_name="가격 B (당일)",
            ),
        ),
    ]
