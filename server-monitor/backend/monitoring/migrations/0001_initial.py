import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AppSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("singleton_key", models.PositiveSmallIntegerField(default=1, editable=False, unique=True)),
                ("check_interval_seconds", models.PositiveIntegerField(default=60, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(3600)])),
                ("ping_timeout_seconds", models.FloatField(default=3.0, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(30)])),
                ("ping_count", models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("http_timeout_seconds", models.FloatField(default=5.0, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(60)])),
                ("smtp_host", models.CharField(blank=True, default="smtp.gmail.com", max_length=255)),
                ("smtp_port", models.PositiveIntegerField(default=587)),
                ("smtp_user", models.CharField(blank=True, max_length=255)),
                ("smtp_password", models.CharField(blank=True, max_length=255)),
                ("smtp_from", models.EmailField(blank=True, max_length=254)),
                ("alert_email_to", models.EmailField(blank=True, max_length=254)),
                ("notify_recovery", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Ajuste de aplicacion",
                "verbose_name_plural": "Ajustes de aplicacion",
            },
        ),
        migrations.CreateModel(
            name="Server",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128)),
                ("ip_address", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("check_ping", models.BooleanField(default=True)),
                ("check_ssh", models.BooleanField(default=True)),
                ("ssh_port", models.PositiveIntegerField(default=22, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(65535)])),
                ("check_http", models.BooleanField(default=False)),
                ("http_url", models.URLField(blank=True)),
                ("check_https", models.BooleanField(default=False)),
                ("https_url", models.URLField(blank=True)),
                ("custom_ports", models.CharField(blank=True, help_text="Lista separada por comas. Ejemplo: 25, 3306, 8080", max_length=255)),
                ("last_status", models.CharField(choices=[("unknown", "Desconocido"), ("up", "Operativo"), ("down", "Caido")], default="unknown", max_length=16)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("last_response_ms", models.FloatField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="CheckLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("check_type", models.CharField(choices=[("ping", "Ping ICMP"), ("ssh", "SSH"), ("http", "HTTP"), ("https", "HTTPS"), ("port", "Puerto")], max_length=16)),
                ("target", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("up", "Operativo"), ("down", "Caido")], max_length=16)),
                ("response_ms", models.FloatField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("checked_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("server", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="check_logs", to="monitoring.server")),
            ],
            options={
                "ordering": ["-checked_at"],
                "indexes": [
                    models.Index(fields=["server", "-checked_at"], name="monitoring__server__a246de_idx"),
                    models.Index(fields=["status", "-checked_at"], name="monitoring__status_fd65bb_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Incident",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("check_type", models.CharField(choices=[("ping", "Ping ICMP"), ("ssh", "SSH"), ("http", "HTTP"), ("https", "HTTPS"), ("port", "Puerto")], max_length=16)),
                ("target", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("open", "Abierta"), ("resolved", "Resuelta")], default="open", max_length=16)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("notified_at", models.DateTimeField(blank=True, null=True)),
                ("recovery_notified_at", models.DateTimeField(blank=True, null=True)),
                ("server", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incidents", to="monitoring.server")),
            ],
            options={
                "ordering": ["-started_at"],
                "indexes": [
                    models.Index(fields=["status", "-started_at"], name="monitoring__status_78de4e_idx"),
                    models.Index(fields=["server", "check_type", "target", "status"], name="monitoring__server__614a2b_idx"),
                ],
            },
        ),
    ]
