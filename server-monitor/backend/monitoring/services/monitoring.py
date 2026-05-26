import logging
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from monitoring.models import (
    AppSetting,
    CheckLog,
    CheckStatus,
    Incident,
    IncidentStatus,
    Server,
    ServerStatus,
)
from monitoring.services.checks import ServiceCheckResult, run_configured_checks
from monitoring.services.emailing import send_incident_email, send_recovery_email


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MonitoringRunResult:
    server: Server
    overall_status: str
    checked_at: object
    logs: list[CheckLog]
    error: str
    response_ms: float | None


def run_server_checks(server: Server, send_alerts: bool = True) -> MonitoringRunResult:
    cfg = AppSetting.load()
    checked_at = timezone.now()

    results = run_configured_checks(
        server,
        ping_count=cfg.ping_count,
        ping_timeout=cfg.ping_timeout_seconds,
        http_timeout=cfg.http_timeout_seconds,
    )

    if not results:
        return _mark_without_checks(server, checked_at)

    failed = [result for result in results if not result.success]
    successful_latencies = [
        result.response_ms for result in results if result.response_ms is not None
    ]
    overall_status = ServerStatus.DOWN if failed else ServerStatus.UP
    response_ms = (
        round(sum(successful_latencies) / len(successful_latencies), 2)
        if successful_latencies
        else None
    )
    error = "; ".join(f"{item.check_type}: {item.error}" for item in failed)[:1000]

    with transaction.atomic():
        logs = [
            CheckLog.objects.create(
                server=server,
                check_type=result.check_type,
                target=result.target,
                status=CheckStatus.UP if result.success else CheckStatus.DOWN,
                response_ms=result.response_ms,
                error_message=result.error,
                checked_at=checked_at,
            )
            for result in results
        ]

        Server.objects.filter(pk=server.pk).update(
            last_status=overall_status,
            last_checked_at=checked_at,
            last_response_ms=response_ms,
            last_error=error,
            updated_at=checked_at,
        )

        for result in results:
            _sync_incident(server, result, checked_at, send_alerts=send_alerts)

    server.refresh_from_db()
    logger.info("Servidor %s comprobado: %s", server.name, overall_status)
    return MonitoringRunResult(server, overall_status, checked_at, logs, error, response_ms)


def run_monitoring_round() -> int:
    total = 0
    for server in Server.objects.filter(is_active=True).order_by("name"):
        try:
            run_server_checks(server, send_alerts=True)
            total += 1
        except Exception:
            logger.exception("Error comprobando servidor id=%s", server.pk)
    return total


def _mark_without_checks(server: Server, checked_at) -> MonitoringRunResult:
    Server.objects.filter(pk=server.pk).update(
        last_status=ServerStatus.UNKNOWN,
        last_checked_at=checked_at,
        last_response_ms=None,
        last_error="Sin comprobaciones habilitadas",
        updated_at=checked_at,
    )
    server.refresh_from_db()
    return MonitoringRunResult(
        server=server,
        overall_status=ServerStatus.UNKNOWN,
        checked_at=checked_at,
        logs=[],
        error=server.last_error,
        response_ms=None,
    )


def _sync_incident(
    server: Server,
    result: ServiceCheckResult,
    checked_at,
    send_alerts: bool,
) -> None:
    open_incident = Incident.objects.filter(
        server=server,
        check_type=result.check_type,
        target=result.target,
        status=IncidentStatus.OPEN,
    ).first()

    if result.success:
        if not open_incident:
            return
        open_incident.status = IncidentStatus.RESOLVED
        open_incident.resolved_at = checked_at
        open_incident.save(update_fields=["status", "resolved_at"])
        if send_alerts and send_recovery_email(open_incident):
            open_incident.recovery_notified_at = timezone.now()
            open_incident.save(update_fields=["recovery_notified_at"])
        return

    if open_incident:
        open_incident.error_message = result.error
        update_fields = ["error_message"]
        if send_alerts and open_incident.notified_at is None and send_incident_email(open_incident):
            open_incident.notified_at = timezone.now()
            update_fields.append("notified_at")
        open_incident.save(update_fields=update_fields)
        return

    incident = Incident.objects.create(
        server=server,
        check_type=result.check_type,
        target=result.target,
        status=IncidentStatus.OPEN,
        error_message=result.error,
        started_at=checked_at,
    )
    if send_alerts and send_incident_email(incident):
        incident.notified_at = timezone.now()
        incident.save(update_fields=["notified_at"])
