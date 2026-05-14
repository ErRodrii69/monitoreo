"""
=============================================================
app/models/__init__.py — Modelos de base de datos (ORM)

Define las tablas del proyecto:
  · Server   → servidores gestionados
  · CheckLog → registro histórico de comprobaciones
=============================================================
"""

from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Enum, Float,
    ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.datetime_utils import utc_now


def _utcnow() -> datetime:
    """Devuelve la hora actual en UTC (compatible con Python 3.11+)."""
    return utc_now()


# ---------------------------------------------------------------------------
# Tabla: servers
# ---------------------------------------------------------------------------

class Server(Base):
    """
    Representa un servidor monitorizado.
    Cada servidor tiene una dirección IP o hostname al que se le
    realizan comprobaciones periódicas de ping ICMP.
    """

    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # --- Identificación ---
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Estado operativo ---
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Estado calculado en el último ciclo de monitorización
    last_status: Mapped[str] = mapped_column(
        Enum("unknown", "up", "down", name="server_status"),
        default="unknown",
        nullable=False,
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_response_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Metadatos ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # --- Relaciones ---
    check_logs: Mapped[list["CheckLog"]] = relationship(
        back_populates="server", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Server id={self.id} name={self.name!r} ip={self.ip_address!r}>"


# ---------------------------------------------------------------------------
# Tabla: check_logs
# ---------------------------------------------------------------------------

class CheckLog(Base):
    """
    Registro histórico de cada comprobación realizada a un servidor.
    Se almacena una fila por cada ping ejecutado, lo que permite
    generar estadísticas de disponibilidad y ver el historial de incidencias.
    """

    __tablename__ = "check_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Resultado ---
    status: Mapped[str] = mapped_column(
        Enum("up", "down", name="check_status"), nullable=False
    )
    response_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Marca de tiempo ---
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    # --- Relaciones ---
    server: Mapped["Server"] = relationship(back_populates="check_logs")

    def __repr__(self) -> str:
        return (
            f"<CheckLog id={self.id} server_id={self.server_id} "
            f"status={self.status!r} checked_at={self.checked_at}>"
        )
