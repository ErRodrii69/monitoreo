from rest_framework import serializers

from .models import AppSetting, CheckLog, Incident, Server


def normalize_custom_ports(value: str) -> str:
    ports: list[int] = []
    for raw_port in (value or "").split(","):
        raw_port = raw_port.strip()
        if not raw_port:
            continue
        if not raw_port.isdigit():
            raise serializers.ValidationError("Los puertos deben ser numericos.")
        port = int(raw_port)
        if port < 1 or port > 65535:
            raise serializers.ValidationError("Cada puerto debe estar entre 1 y 65535.")
        if port not in ports:
            ports.append(port)
    return ", ".join(str(port) for port in ports)


class ServerSerializer(serializers.ModelSerializer):
    service_summary = serializers.SerializerMethodField()

    class Meta:
        model = Server
        fields = [
            "id",
            "name",
            "ip_address",
            "description",
            "is_active",
            "check_ping",
            "check_ssh",
            "ssh_port",
            "check_http",
            "http_url",
            "check_https",
            "https_url",
            "custom_ports",
            "service_summary",
            "last_status",
            "last_checked_at",
            "last_response_ms",
            "last_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "last_status",
            "last_checked_at",
            "last_response_ms",
            "last_error",
            "created_at",
            "updated_at",
            "service_summary",
        ]

    def validate_ip_address(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("La IP o hostname es obligatorio.")
        if any(char.isspace() for char in value):
            raise serializers.ValidationError("La IP o hostname no puede contener espacios.")
        return value

    def validate_custom_ports(self, value: str) -> str:
        return normalize_custom_ports(value)

    def validate(self, attrs):
        instance = self.instance
        merged = {
            "is_active": attrs.get("is_active", getattr(instance, "is_active", True)),
            "check_ping": attrs.get("check_ping", getattr(instance, "check_ping", True)),
            "check_ssh": attrs.get("check_ssh", getattr(instance, "check_ssh", True)),
            "check_http": attrs.get("check_http", getattr(instance, "check_http", False)),
            "check_https": attrs.get("check_https", getattr(instance, "check_https", False)),
            "custom_ports": attrs.get("custom_ports", getattr(instance, "custom_ports", "")),
        }
        has_checks = any(
            [
                merged["check_ping"],
                merged["check_ssh"],
                merged["check_http"],
                merged["check_https"],
                bool(normalize_custom_ports(merged["custom_ports"])),
            ]
        )
        if merged["is_active"] and not has_checks:
            raise serializers.ValidationError(
                "Un servidor activo necesita al menos una comprobacion."
            )
        return attrs

    def get_service_summary(self, obj: Server) -> list[str]:
        services: list[str] = []
        if obj.check_ping:
            services.append("Ping")
        if obj.check_ssh:
            services.append(f"SSH:{obj.ssh_port}")
        if obj.check_http:
            services.append("HTTP")
        if obj.check_https:
            services.append("HTTPS")
        services.extend([f":{port}" for port in obj.custom_port_list()])
        return services


class CheckLogSerializer(serializers.ModelSerializer):
    server_id = serializers.IntegerField(source="server.id", read_only=True)
    server_name = serializers.CharField(source="server.name", read_only=True)

    class Meta:
        model = CheckLog
        fields = [
            "id",
            "server_id",
            "server_name",
            "check_type",
            "target",
            "status",
            "response_ms",
            "error_message",
            "checked_at",
        ]


class IncidentSerializer(serializers.ModelSerializer):
    server_id = serializers.IntegerField(source="server.id", read_only=True)
    server_name = serializers.CharField(source="server.name", read_only=True)

    class Meta:
        model = Incident
        fields = [
            "id",
            "server_id",
            "server_name",
            "check_type",
            "target",
            "status",
            "error_message",
            "started_at",
            "resolved_at",
            "notified_at",
        ]


class AppSettingSerializer(serializers.ModelSerializer):
    smtp_password = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )

    class Meta:
        model = AppSetting
        fields = [
            "check_interval_seconds",
            "ping_timeout_seconds",
            "ping_count",
            "http_timeout_seconds",
            "alert_email_to",
            "smtp_host",
            "smtp_port",
            "smtp_user",
            "smtp_password",
            "smtp_from",
            "notify_recovery",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def update(self, instance, validated_data):
        if validated_data.get("smtp_password") == "":
            validated_data.pop("smtp_password", None)
        return super().update(instance, validated_data)


class ManualCheckResponseSerializer(serializers.Serializer):
    server_id = serializers.IntegerField()
    server_name = serializers.CharField()
    ip_address = serializers.CharField()
    success = serializers.BooleanField()
    last_status = serializers.CharField()
    response_ms = serializers.FloatField(allow_null=True)
    error = serializers.CharField(allow_blank=True)
    checked_at = serializers.DateTimeField()
    checks = CheckLogSerializer(many=True)
