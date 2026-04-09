from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_productoptionitem_audience_image_tier"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productoptionitem",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="products/option_items/",
                verbose_name="상품 이미지",
            ),
        ),
    ]
