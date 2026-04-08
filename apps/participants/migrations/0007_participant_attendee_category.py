# Generated manually for attendee_category

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("participants", "0006_rename_table_to_participants"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="attendee_category",
            field=models.CharField(
                choices=[
                    ("ADULT", "성인 (Adult)"),
                    ("YOUTH", "청소년 (Youth)"),
                    ("CHILDREN", "어린이 (Children)"),
                    ("VOLUNTEER", "발렌티어 (Volunteer)"),
                    ("B2N_STAFF", "스태프 (B2N Staff)"),
                ],
                db_comment="참석자 구분",
                default="ADULT",
                help_text="성인·청소년·어린이·발렌티어·스태프",
                max_length=20,
                verbose_name="참석자 구분",
            ),
        ),
    ]
