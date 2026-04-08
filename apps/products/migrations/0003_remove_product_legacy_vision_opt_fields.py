from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0002_product_option_items_and_applications"),
    ]

    operations = [
        migrations.RemoveField(model_name="product", name="opt_not_participating_enabled"),
        migrations.RemoveField(model_name="product", name="opt_not_participating_price"),
        migrations.RemoveField(model_name="product", name="opt_before_b2n_enabled"),
        migrations.RemoveField(model_name="product", name="opt_before_b2n_price"),
        migrations.RemoveField(model_name="product", name="opt_after_b2n_enabled"),
        migrations.RemoveField(model_name="product", name="opt_after_b2n_price"),
    ]
