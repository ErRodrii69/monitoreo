"""
=============================================================
app/services/monitor_service.py — Orquestador de monitorización

Responsabilidad: coordinar el ciclo completo de comprobación
para un único servidor:
  1. Ejecutar el ping (ping_service)
  2. Actualizar el estado en BD
  3. Registrar el log de comprobación
  4. Enviar correo de alerta si el servidor ha caído (email_service)

Cada una de esas responsabilidades está delegada en su propio
módulo; este servicio solo las combina.
=============================================================
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Server, CheckLog
from app.core.datetime_utils import utc_now
from app.services.ping_service import ping_host
from app.services.email_service import send_alert_email
from app.core.config import get_settings


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CheckExecutionResult:
    """Structured result for a persisted server check."""

    status: str
    response_ms: float | None
    error_message: str | None
    checked_at: datetime


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

async def check_server(
    server: Server,
    db: AsyncSession,
    send_alerts: bool = True,
) -> CheckExecutionResult:
    """
    Realiza la comprobación completa de un servidor.

    Parámetros:
        server — Instancia ORM del servidor a comprobar.
        db     — Sesión de BD activa (inyectada por el scheduler).

    Flujo:
        ping → guardar resultado en check_logs
             → actualizar last_status en servers
             → si acaba de caer: enviar email de alerta
    """

    cfg = get_settings()

    # 1. Ejecutar ping
    result = await ping_host(
        host=server.ip_address,
        count=cfg.ping_count,
        timeout=cfg.ping_timeout_seconds,
    )

    now = utc_now()
    new_status = "up" if result.success else "down"
    previous_status = server.last_status

    # 2. Guardar log de la comprobación
    await _save_check_log(
        db=db,
        server_id=server.id,
        status=new_status,
        response_ms=result.response_ms,
        error_message=result.error,
        checked_at=now,
    )

    # 3. Actualizar el estado actual del servidor
    await _update_server_status(
        db=db,
        server=server,
        status=new_status,
        response_ms=result.response_ms,
        checked_at=now,
    )

    logger.info(
        "Server '%s' (%s): %s (%.1f ms)",
        server.name,
        server.ip_address,
        new_status,
        result.response_ms or 0.0,
    )

    # 4. Enviar alerta solo cuando el servidor acaba de caer
    #    (evitamos spam si lleva varios ciclos caído)
    if send_alerts and new_status == "down" and previous_status != "down":
        logger.warning(
            "Servidor '%s' (%s) ha caído. Enviando alerta por correo.",
            server.name,
            server.ip_address,
        )
        await send_alert_email(
            server_name=server.name,
            ip_address=server.ip_address,
            error_message=result.error or "Sin respuesta al ping ICMP",
            checked_at=now,
        )

    return CheckExecutionResult(
        status=new_status,
        response_ms=result.response_ms,
        error_message=result.error,
        checked_at=now,
    )


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

async def _save_check_log(
    db: AsyncSession,
    server_id: int,
    status: str,
    response_ms: float | None,
    error_message: str | None,
    checked_at: datetime,
) -> None:
    """
    Inserta una fila en check_logs con el resultado de la comprobación.
    Responsabilidad única: escritura del log.
    """
    log = CheckLog(
        server_id=server_id,
        status=status,
        response_ms=response_ms,
        error_message=error_message,
        checked_at=checked_at,
    )
    db.add(log)
    await db.flush()


async def _update_server_status(
    db: AsyncSession,
    server: Server,
    status: str,
    response_ms: float | None,
    checked_at: datetime,
) -> None:
    """
    Actualiza los campos de estado del servidor en la tabla 'servers'.
    Responsabilidad única: actualización del registro del servidor.
    """
    server.last_status = status
    server.last_response_ms = response_ms
    server.last_checked_at = checked_at
    await db.flush()
