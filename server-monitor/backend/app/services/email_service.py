"""
=============================================================
app/services/email_service.py — Envío de notificaciones por correo

Responsabilidad única: enviar correos electrónicos de alerta.
No toca la base de datos ni ejecuta pings.

Usa aiosmtplib para enviar de forma asíncrona sin bloquear el
event loop. Si las credenciales SMTP no están configuradas, la
función registra un aviso en el log y no intenta conectarse.
=============================================================
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import aiosmtplib

from app.core.config import get_settings
from app.core.datetime_utils import format_datetime_in_spain


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

async def send_alert_email(
    server_name: str,
    ip_address: str,
    error_message: str,
    checked_at: datetime,
) -> None:
    """
    Envía un correo de alerta indicando que un servidor ha caído.

    Parámetros:
        server_name   — Nombre legible del servidor.
        ip_address    — IP o hostname del servidor caído.
        error_message — Descripción del error detectado.
        checked_at    — Momento en que se detectó el fallo.

    El correo se envía a la dirección configurada en ALERT_EMAIL_TO.
    Si no hay credenciales SMTP configuradas, se omite el envío y
    se deja constancia en el log.
    """

    cfg = get_settings()

    # Guardamos verificar que las credenciales mínimas están presentes
    if not cfg.smtp_user or not cfg.alert_email_to:
        logger.warning(
            "Email no enviado: faltan SMTP_USER o ALERT_EMAIL_TO en la configuración."
        )
        return

    subject, html_body, text_body = _build_email_content(
        server_name, ip_address, error_message, checked_at
    )

    message = _build_mime_message(
        from_addr=cfg.smtp_from or cfg.smtp_user,
        to_addr=cfg.alert_email_to,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=cfg.smtp_host,
            port=cfg.smtp_port,
            username=cfg.smtp_user,
            password=cfg.smtp_password,
            start_tls=True,
        )
        logger.info(
            "Alerta enviada a %s — servidor: %s (%s)",
            cfg.alert_email_to, server_name, ip_address,
        )
    except Exception as exc:
        # El fallo de envío nunca debe tirar la monitorización principal
        logger.error("Error enviando correo de alerta: %s", exc)


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _build_email_content(
    server_name: str,
    ip_address: str,
    error_message: str,
    checked_at: datetime,
) -> tuple[str, str, str]:
    """
    Construye el asunto, el cuerpo HTML y el cuerpo en texto plano del correo.

    Devuelve una tupla (subject, html_body, text_body).
    """

    timestamp = format_datetime_in_spain(checked_at)
    subject = f"⚠️ ALERTA: Servidor '{server_name}' caído"

    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
      <h2 style="color: #c0392b;">⚠️ Servidor caído</h2>
      <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        <tr>
          <td style="padding: 8px; font-weight: bold; background: #f2f2f2;">Servidor</td>
          <td style="padding: 8px;">{server_name}</td>
        </tr>
        <tr>
          <td style="padding: 8px; font-weight: bold; background: #f2f2f2;">IP / Host</td>
          <td style="padding: 8px;">{ip_address}</td>
        </tr>
        <tr>
          <td style="padding: 8px; font-weight: bold; background: #f2f2f2;">Error</td>
          <td style="padding: 8px; color: #c0392b;">{error_message}</td>
        </tr>
        <tr>
          <td style="padding: 8px; font-weight: bold; background: #f2f2f2;">Detectado a las</td>
          <td style="padding: 8px;">{timestamp}</td>
        </tr>
      </table>
      <p style="margin-top: 20px; font-size: 12px; color: #888;">
        Este mensaje ha sido generado automáticamente por el Sistema de Monitorización.
      </p>
    </body></html>
    """

    text_body = (
        f"ALERTA: Servidor caído\n"
        f"Servidor : {server_name}\n"
        f"IP / Host: {ip_address}\n"
        f"Error    : {error_message}\n"
        f"Hora     : {timestamp}\n"
    )

    return subject, html_body, text_body


def _build_mime_message(
    from_addr: str,
    to_addr: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> MIMEMultipart:
    """
    Construye el objeto MIMEMultipart listo para ser enviado.
    Incluye tanto la versión en texto plano como la HTML (multipart/alternative).
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg
