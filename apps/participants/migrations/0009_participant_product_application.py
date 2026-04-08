import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_remove_product_legacy_vision_opt_fields"),
        ("participants", "0008_participant_passport_copy"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="product_application",
            field=models.ForeignKey(
                blank=True,
                help_text="www 등록 시 공개 신청 API로 생성된 ProductApplication",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="participants",
                to="products.productapplication",
                verbose_name="상품 신청(금액 스냅샷)",
            ),
        ),
    ]
