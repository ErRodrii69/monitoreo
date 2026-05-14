"""
=============================================================
app/api/schemas.py — Esquemas Pydantic (request / response)

Validan y serializan los datos que entran y salen de la API.
Separados de los modelos ORM para respetar el principio de
responsabilidad única.
=============================================================
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.core.datetime_utils import ensure_utc, serialize_datetime


# ---------------------------------------------------------------------------
# Servidor
# ---------------------------------------------------------------------------

class ServerCreate(BaseModel):
    """Datos necesarios para crear un nuevo servidor."""

    name: str = Field(..., min_length=1, max_length=128, description="Nombre legible del servidor")
    ip_address: str = Field(..., description="Dirección IP o hostname del servidor")
    description: Optional[str] = Field(None, max_length=500, description="Descripción opcional")
    is_active: bool = Field(True, description="Si False el servidor no se monitoriza")

    @field_validator("ip_address")
    @classmethod
    def validate_ip_or_hostname(cls, v: str) -> str:
        """
        Acepta IPv4, IPv6 y hostnames válidos.
        Rechaza cadenas vacías o con espacios.
        """
        v = v.strip()
        if not v:
            raise ValueError("ip_address no puede estar vacío")
        # Validación básica: no contiene espacios
        if " " in v:
            raise ValueError("ip_address no puede contener espacios")
        return v


class ServerUpdate(BaseModel):
    """Campos actualizables de un servidor. Todos son opcionales."""

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    ip_address: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ServerOut(BaseModel):
    """Representación completa de un servidor para las respuestas de la API."""

    id: int
    name: str
    ip_address: str
    description: Optional[str]
    is_active: bool
    last_status: str
    last_checked_at: Optional[datetime]
    last_response_ms: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("last_checked_at", "created_at", "updated_at", mode="before")
    @classmethod
    def normalize_dt(cls, value: Optional[datetime]) -> datetime | None:
        return ensure_utc(value)

    @field_serializer("last_checked_at", "created_at", "updated_at", when_used="json")
    def serialize_dt(self, value: Optional[datetime]) -> str | None:
        return serialize_datetime(value)


# ---------------------------------------------------------------------------
# Log de comprobación
# ---------------------------------------------------------------------------

class CheckLogOut(BaseModel):
    """Representación de un registro de comprobación."""

    id: int
    server_id: int
    status: str
    response_ms: Optional[float]
    error_message: Optional[str]
    checked_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("checked_at", mode="before")
    @classmethod
    def normalize_dt(cls, value: datetime) -> datetime:
        normalized = ensure_utc(value)
        assert normalized is not None
        return normalized

    @field_serializer("checked_at", when_used="json")
    def serialize_dt(self, value: datetime) -> str:
        serialized = serialize_datetime(value)
        assert serialized is not None
        return serialized


class ManualPingOut(BaseModel):
    """Resultado de una comprobacion manual persistida."""

    server_id: int
    server_name: str
    ip_address: str
    success: bool
    last_status: str
    response_ms: Optional[float]
    error: Optional[str]
    checked_at: datetime

    @field_validator("checked_at", mode="before")
    @classmethod
    def normalize_dt(cls, value: datetime) -> datetime:
        normalized = ensure_utc(value)
        assert normalized is not None
        return normalized

    @field_serializer("checked_at", when_used="json")
    def serialize_dt(self, value: datetime) -> str:
        serialized = serialize_datetime(value)
        assert serialized is not None
        return serialized


# ---------------------------------------------------------------------------
# Ajustes de la aplicación
# ---------------------------------------------------------------------------

class AppSettings(BaseModel):
    """Ajustes globales editables en tiempo real desde la UI."""

    check_interval_seconds: int = Field(
        ...,
        ge=10,
        le=3600,
        description="Intervalo entre rondas de ping (10–3600 segundos)",
    )
    alert_email_to: str = Field(..., description="Correo destino de las alertas")
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from: str


class AppSettingsUpdate(BaseModel):
    """Campos actualizables de los ajustes. Todos son opcionales."""

    check_interval_seconds: Optional[int] = Field(None, ge=10, le=3600)
    alert_email_to: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
