# Generated manually — apply with: python manage.py migrate

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="상품명")),
                ("description", models.TextField(blank=True, default="", verbose_name="상품 설명(HTML)")),
                ("base_price", models.DecimalField(decimal_places=0, max_digits=12, verbose_name="기본 가격")),
                (
                    "status",
                    models.CharField(
                        choices=[("ACTIVE", "ACTIVE"), ("INACTIVE", "INACTIVE")],
                        default="ACTIVE",
                        max_length=10,
                        verbose_name="상태",
                    ),
                ),
                ("opt_not_participating_enabled", models.BooleanField(default=False)),
                ("opt_not_participating_price", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("opt_before_b2n_enabled", models.BooleanField(default=False)),
                ("opt_before_b2n_price", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("opt_after_b2n_enabled", models.BooleanField(default=False)),
                ("opt_after_b2n_price", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("application_start", models.DateTimeField(blank=True, null=True, verbose_name="신청 시작")),
                ("application_end", models.DateTimeField(blank=True, null=True, verbose_name="신청 종료")),
                ("event_start", models.DateTimeField(blank=True, null=True, verbose_name="행사 시작")),
                ("event_end", models.DateTimeField(blank=True, null=True, verbose_name="행사 종료")),
                (
                    "thumbnail",
                    models.ImageField(blank=True, null=True, upload_to="products/thumbnails/", verbose_name="썸네일"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "상품",
                "verbose_name_plural": "상품",
                "db_table": "products",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ProductDetailImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="products/detail/")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="detail_images",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "db_table": "product_detail_images",
                "ordering": ["sort_order", "id"],
            },
        ),
    ]
