from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0002_readable_table_names"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="checklog",
            old_name="monitoring__server__a246de_idx",
            new_name="check_logs_server__ae62e1_idx",
        ),
        migrations.RenameIndex(
            model_name="checklog",
            old_name="monitoring__status_fd65bb_idx",
            new_name="check_logs_status_5a4bab_idx",
        ),
        migrations.RenameIndex(
            model_name="incident",
            old_name="monitoring__status_78de4e_idx",
            new_name="incidents_status_604ac3_idx",
        ),
        migrations.RenameIndex(
            model_name="incident",
            old_name="monitoring__server__614a2b_idx",
            new_name="incidents_server__f43998_idx",
        ),
    ]
