from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0005_alter_productoptionitem_image_verbose_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="productoptionitem",
            name="image_s3_key",
            field=models.CharField(
                blank=True,
                default="",
                help_text="S3 또는 로컬 MEDIA 경로 키 (product-option-items/...). PlanDoc/s3Rules.md",
                max_length=1024,
                verbose_name="상품 이미지 객체 키",
            ),
        ),
        migrations.AlterField(
            model_name="productoptionitem",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="products/option_items/",
                verbose_name="상품 이미지(레거시)",
            ),
        ),
    ]
