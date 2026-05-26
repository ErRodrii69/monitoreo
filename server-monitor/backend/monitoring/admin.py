from django.contrib import admin

from .models import AppSetting, CheckLog, Incident, Server


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "ip_address", "is_active", "last_status", "last_checked_at")
    list_filter = ("is_active", "last_status", "check_ping", "check_ssh", "check_http", "check_https")
    search_fields = ("name", "ip_address", "description")


@admin.register(CheckLog)
class CheckLogAdmin(admin.ModelAdmin):
    list_display = ("checked_at", "server", "check_type", "target", "status", "response_ms")
    list_filter = ("status", "check_type", "checked_at")
    search_fields = ("server__name", "target", "error_message")
    readonly_fields = ("checked_at",)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("server", "check_type", "target", "status", "started_at", "resolved_at")
    list_filter = ("status", "check_type", "started_at")
    search_fields = ("server__name", "target", "error_message")


@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ("check_interval_seconds", "alert_email_to", "smtp_host", "notify_recovery", "updated_at")

    def has_add_permission(self, request):
        return not AppSetting.objects.exists()
