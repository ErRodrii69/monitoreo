import logging

from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone

from monitoring.models import AppSetting, Incident


logger = logging.getLogger(__name__)


def send_incident_email(incident: Incident) -> bool:
    cfg = AppSetting.load()
    if not _email_configured(cfg):
        logger.warning("Email omitido: faltan SMTP_USER o ALERT_EMAIL_TO.")
        return False

    subject = f"ALERTA: {incident.server.name} falla en {incident.check_type.upper()}"
    text_body = (
        "Incidencia detectada\n"
        f"Servidor: {incident.server.name}\n"
        f"Host: {incident.server.ip_address}\n"
        f"Comprobacion: {incident.check_type}\n"
        f"Objetivo: {incident.target}\n"
        f"Error: {incident.error_message}\n"
        f"Hora: {timezone.localtime(incident.started_at).strftime('%d/%m/%Y %H:%M:%S')}\n"
    )
    html_body = text_body.replace("\n", "<br>")
    return _send(cfg, subject, text_body, html_body)


def send_recovery_email(incident: Incident) -> bool:
    cfg = AppSetting.load()
    if not cfg.notify_recovery or not _email_configured(cfg):
        return False

    resolved_at = incident.resolved_at or timezone.now()
    subject = f"RECUPERADO: {incident.server.name} en {incident.check_type.upper()}"
    text_body = (
        "Incidencia resuelta\n"
        f"Servidor: {incident.server.name}\n"
        f"Host: {incident.server.ip_address}\n"
        f"Comprobacion: {incident.check_type}\n"
        f"Objetivo: {incident.target}\n"
        f"Inicio: {timezone.localtime(incident.started_at).strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"Recuperacion: {timezone.localtime(resolved_at).strftime('%d/%m/%Y %H:%M:%S')}\n"
    )
    html_body = text_body.replace("\n", "<br>")
    return _send(cfg, subject, text_body, html_body)


def _email_configured(cfg: AppSetting) -> bool:
    return bool(cfg.smtp_host and cfg.smtp_user and cfg.alert_email_to)


def _send(cfg: AppSetting, subject: str, text_body: str, html_body: str) -> bool:
    connection = get_connection(
        host=cfg.smtp_host,
        port=cfg.smtp_port,
        username=cfg.smtp_user,
        password=cfg.smtp_password,
        use_tls=True,
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=cfg.smtp_from or cfg.smtp_user,
        to=[cfg.alert_email_to],
        connection=connection,
    )
    message.attach_alternative(html_body, "text/html")

    try:
        message.send()
    except Exception as exc:
        logger.error("No se pudo enviar el email: %s", exc)
        return False

    return True
