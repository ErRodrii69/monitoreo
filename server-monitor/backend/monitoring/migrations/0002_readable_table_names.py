from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelTable(name="appsetting", table="app_settings"),
        migrations.AlterModelTable(name="checklog", table="check_logs"),
        migrations.AlterModelTable(name="incident", table="incidents"),
        migrations.AlterModelTable(name="server", table="servers"),
    ]
