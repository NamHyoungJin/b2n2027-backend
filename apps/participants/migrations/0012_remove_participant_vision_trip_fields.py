from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("participants", "0011_participant_status_workflow"),
    ]

    operations = [
        migrations.RemoveField(model_name="participant", name="vision_trip_cappadocia"),
        migrations.RemoveField(model_name="participant", name="vision_trip_antioch"),
        migrations.RemoveField(model_name="participant", name="vision_trip_istanbul"),
        migrations.RemoveField(model_name="participant", name="vision_trip_choice"),
    ]
