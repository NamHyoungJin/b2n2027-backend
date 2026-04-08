# Generated manually — apply with: python manage.py migrate

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductOptionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("price_before", models.DecimalField(decimal_places=0, max_digits=12)),
                ("price_after", models.DecimalField(decimal_places=0, max_digits=12)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="option_items",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "상품 옵션(코스)",
                "verbose_name_plural": "상품 옵션(코스)",
                "db_table": "product_option_items",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="ProductApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "participation_type",
                    models.CharField(
                        choices=[
                            ("BEFORE_B2N", "BEFORE_B2N"),
                            ("AFTER_B2N", "AFTER_B2N"),
                            ("NOT_PARTICIPATING", "NOT_PARTICIPATING"),
                        ],
                        max_length=20,
                    ),
                ),
                ("total_amount", models.DecimalField(decimal_places=0, max_digits=14)),
                (
                    "client_total_amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=0,
                        help_text="클라이언트가 보낸 합계(감사·검증용, 신뢰하지 않음)",
                        max_digits=14,
                        null=True,
                    ),
                ),
                ("applicant_email", models.EmailField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "db_table": "product_applications",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ApplicationOptionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("selected_price", models.DecimalField(decimal_places=0, max_digits=12)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="option_lines",
                        to="products.productapplication",
                    ),
                ),
                (
                    "option_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="application_lines",
                        to="products.productoptionitem",
                    ),
                ),
            ],
            options={
                "db_table": "application_option_items",
                "ordering": ["id"],
            },
        ),
    ]
