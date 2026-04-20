from django.db import migrations, models

# homepageDocPlan.md §2 — 마이그레이션에 고정(앱 상수 변경과 무관)
_SEED = (
    ("terms_sensitive", "이용약관(민감정보)"),
    ("privacy_policy", "개인정보취급방침"),
    ("refund_policy", "환불정책"),
    ("travel_insurance", "여행자보험"),
)


def seed_rows(apps, schema_editor):
    HomepageDocInfo = apps.get_model("homepage_doc", "HomepageDocInfo")
    for doc_type, title in _SEED:
        HomepageDocInfo.objects.get_or_create(
            doc_type=doc_type,
            defaults={
                "title": title,
                "body_html": "",
                "is_published": False,
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HomepageDocInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("doc_type", models.CharField(db_index=True, max_length=48, unique=True)),
                ("title", models.CharField(blank=True, max_length=255, null=True)),
                ("body_html", models.TextField(blank=True, default="")),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "homepage_doc_info",
                "ordering": ["doc_type"],
            },
        ),
        migrations.RunPython(seed_rows, noop_reverse),
    ]
