"""
=============================================================
app/api/settings.py — Endpoints de ajustes de la aplicación

GET   /api/settings → obtener ajustes actuales
PATCH /api/settings → actualizar ajustes (incluyendo el intervalo)

El intervalo de monitorización se puede modificar sin reiniciar
el servicio: el scheduler lee el atributo en tiempo real.
=============================================================
"""

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.api.schemas import AppSettings, AppSettingsUpdate


router = APIRouter()


# ---------------------------------------------------------------------------
# GET /api/settings — Obtener ajustes actuales
# ---------------------------------------------------------------------------

@router.get("/", response_model=AppSettings)
async def get_app_settings():
    """
    Devuelve los ajustes actuales de la aplicación.
    La contraseña SMTP nunca se incluye en la respuesta.
    """
    cfg = get_settings()
    return AppSettings(
        check_interval_seconds=cfg.check_interval_seconds,
        alert_email_to=cfg.alert_email_to,
        smtp_host=cfg.smtp_host,
        smtp_port=cfg.smtp_port,
        smtp_user=cfg.smtp_user,
        smtp_from=cfg.smtp_from,
    )


# ---------------------------------------------------------------------------
# PATCH /api/settings — Actualizar ajustes
# ---------------------------------------------------------------------------

@router.patch("/", response_model=AppSettings)
async def update_app_settings(payload: AppSettingsUpdate, request: Request):
    """
    Actualiza en caliente los ajustes de la aplicación.

    El cambio de 'check_interval_seconds' surte efecto en el siguiente
    ciclo de espera del scheduler (sin reiniciar el proceso).

    Nota: los cambios son en memoria; si se reinicia el proceso se
    recuperan los valores del fichero .env. Para persistencia permanente,
    actualiza el .env o la variable de entorno correspondiente.
    """
    cfg = get_settings()
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(cfg, key) and value is not None:
            object.__setattr__(cfg, key, value)

    # Propagamos el nuevo intervalo al scheduler si está corriendo
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler and "check_interval_seconds" in update_data:
        scheduler.interval_seconds = update_data["check_interval_seconds"]

    return AppSettings(
        check_interval_seconds=cfg.check_interval_seconds,
        alert_email_to=cfg.alert_email_to,
        smtp_host=cfg.smtp_host,
        smtp_port=cfg.smtp_port,
        smtp_user=cfg.smtp_user,
        smtp_from=cfg.smtp_from,
    )
