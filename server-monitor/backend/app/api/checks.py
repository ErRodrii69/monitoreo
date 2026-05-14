"""
=============================================================
app/api/checks.py — Endpoints de historial de comprobaciones

GET /api/checks                    → últimas N comprobaciones globales
GET /api/checks/server/{server_id} → historial de un servidor concreto
=============================================================
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import CheckLog
from app.api.schemas import CheckLogOut


router = APIRouter()


# ---------------------------------------------------------------------------
# GET /api/checks — Últimas comprobaciones globales
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[CheckLogOut])
async def list_recent_checks(
    limit: int = Query(50, ge=1, le=500, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve las últimas *limit* comprobaciones de todos los servidores,
    ordenadas de más reciente a más antigua.
    Útil para el feed de incidencias en tiempo real de la pantalla principal.
    """
    result = await db.execute(
        select(CheckLog)
        .order_by(desc(CheckLog.checked_at))
        .limit(limit)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /api/checks/server/{server_id} — Historial de un servidor
# ---------------------------------------------------------------------------

@router.get("/server/{server_id}", response_model=list[CheckLogOut])
async def list_server_checks(
    server_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve el historial de comprobaciones de un servidor específico,
    ordenado de más reciente a más antiguo.
    """
    result = await db.execute(
        select(CheckLog)
        .where(CheckLog.server_id == server_id)
        .order_by(desc(CheckLog.checked_at))
        .limit(limit)
    )
    return result.scalars().all()
