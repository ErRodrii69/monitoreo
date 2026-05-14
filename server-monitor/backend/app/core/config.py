"""
=============================================================
app/core/config.py — Configuración centralizada

Lee las variables de entorno (o el fichero .env) usando
Pydantic Settings. Un único punto de verdad para toda la app.
=============================================================
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Parámetros de configuración de la aplicación.
    Todos los valores pueden sobreescribirse mediante variables de entorno
    o un fichero .env en la raíz del backend.
    """

    # --- Base de datos ---
    database_url: str = "postgresql+asyncpg://monitor:monitor@db:5432/servermonitor"

    # --- Correo electrónico ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    alert_email_to: str = ""          # Dirección destino de alertas

    # --- Scheduler ---
    # Intervalo en segundos entre rondas de comprobación (editable en runtime
    # desde la pantalla de ajustes; este valor es el predeterminado inicial).
    check_interval_seconds: int = 60

    # --- Ping ---
    ping_timeout_seconds: float = 3.0  # Tiempo máx. de espera por ping
    ping_count: int = 1                # Nº de paquetes ICMP por comprobación

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """
    Devuelve la instancia singleton de Settings.
    El decorador lru_cache garantiza que el fichero .env
    solo se lee una vez durante la vida del proceso.
    """
    return Settings()
