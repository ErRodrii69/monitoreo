import os

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class ServerStatus(models.TextChoices):
    UNKNOWN = "unknown", "Desconocido"
    UP = "up", "Operativo"
    DOWN = "down", "Caido"


class CheckType(models.TextChoices):
    PING = "ping", "Ping ICMP"
    SSH = "ssh", "SSH"
    HTTP = "http", "HTTP"
    HTTPS = "https", "HTTPS"
    PORT = "port", "Puerto"


class CheckStatus(models.TextChoices):
    UP = "up", "Operativo"
    DOWN = "down", "Caido"


class IncidentStatus(models.TextChoices):
    OPEN = "open", "Abierta"
    RESOLVED = "resolved", "Resuelta"


class Server(models.Model):
    name = models.CharField(max_length=128)
    ip_address = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    check_ping = models.BooleanField(default=True)
    check_ssh = models.BooleanField(default=True)
    ssh_port = models.PositiveIntegerField(
        default=22, validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    check_http = models.BooleanField(default=False)
    http_url = models.URLField(blank=True)
    check_https = models.BooleanField(default=False)
    https_url = models.URLField(blank=True)
    custom_ports = models.CharField(
        max_length=255,
        blank=True,
        help_text="Lista separada por comas. Ejemplo: 25, 3306, 8080",
    )

    last_status = models.CharField(
        max_length=16, choices=ServerStatus.choices, default=ServerStatus.UNKNOWN
    )
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_response_ms = models.FloatField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"

    def custom_port_list(self) -> list[int]:
        ports: list[int] = []
        for raw_port in self.custom_ports.split(","):
            value = raw_port.strip()
            if not value:
                continue
            try:
                port = int(value)
            except ValueError:
                continue
            if 1 <= port <= 65535:
                ports.append(port)
        return ports

    def has_enabled_checks(self) -> bool:
        return any(
            [
                self.check_ping,
                self.check_ssh,
                self.check_http,
                self.check_https,
                bool(self.custom_port_list()),
            ]
        )


class CheckLog(models.Model):
    server = models.ForeignKey(
        Server, related_name="check_logs", on_delete=models.CASCADE
    )
    check_type = models.CharField(max_length=16, choices=CheckType.choices)
    target = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=CheckStatus.choices)
    response_ms = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    checked_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["server", "-checked_at"]),
            models.Index(fields=["status", "-checked_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.server_id} {self.check_type} {self.status}"


class Incident(models.Model):
    server = models.ForeignKey(
        Server, related_name="incidents", on_delete=models.CASCADE
    )
    check_type = models.CharField(max_length=16, choices=CheckType.choices)
    target = models.CharField(max_length=255)
    status = models.CharField(
        max_length=16, choices=IncidentStatus.choices, default=IncidentStatus.OPEN
    )
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(default=timezone.now, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    recovery_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["status", "-started_at"]),
            models.Index(fields=["server", "check_type", "target", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.server.name} {self.check_type} {self.status}"


class AppSetting(models.Model):
    singleton_key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)

    check_interval_seconds = models.PositiveIntegerField(
        default=60, validators=[MinValueValidator(10), MaxValueValidator(3600)]
    )
    ping_timeout_seconds = models.FloatField(
        default=3.0, validators=[MinValueValidator(1), MaxValueValidator(30)]
    )
    ping_count = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    http_timeout_seconds = models.FloatField(
        default=5.0, validators=[MinValueValidator(1), MaxValueValidator(60)]
    )

    smtp_host = models.CharField(max_length=255, blank=True, default="smtp.gmail.com")
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_user = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)
    smtp_from = models.EmailField(blank=True)
    alert_email_to = models.EmailField(blank=True)
    notify_recovery = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ajuste de aplicacion"
        verbose_name_plural = "Ajustes de aplicacion"

    def save(self, *args, **kwargs):
        self.pk = 1
        self.singleton_key = 1
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return "Ajustes de monitorizacion"

    @classmethod
    def load(cls) -> "AppSetting":
        defaults = {
            "check_interval_seconds": settings.MONITOR_DEFAULT_INTERVAL,
            "ping_timeout_seconds": settings.MONITOR_DEFAULT_PING_TIMEOUT,
            "ping_count": settings.MONITOR_DEFAULT_PING_COUNT,
            "http_timeout_seconds": settings.MONITOR_DEFAULT_HTTP_TIMEOUT,
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_user": os.getenv("SMTP_USER", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "smtp_from": os.getenv("SMTP_FROM", ""),
            "alert_email_to": os.getenv("ALERT_EMAIL_TO", ""),
            "notify_recovery": os.getenv("NOTIFY_RECOVERY", "true").lower()
            in {"1", "true", "yes", "on"},
        }
        obj, _ = cls.objects.get_or_create(pk=1, defaults=defaults)
        return obj
