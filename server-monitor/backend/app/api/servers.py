"""
=============================================================
app/api/servers.py — Endpoints CRUD de servidores

GET    /api/servers          → listar todos los servidores
POST   /api/servers          → crear servidor
GET    /api/servers/{id}     → obtener servidor por ID
PUT    /api/servers/{id}     → actualizar servidor
DELETE /api/servers/{id}     → eliminar servidor
POST   /api/servers/{id}/ping → ping manual inmediato
=============================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ManualPingOut, ServerCreate, ServerOut, ServerUpdate
from app.core.database import get_db
from app.models import Server
from app.services.monitor_service import check_server


router = APIRouter()


# ---------------------------------------------------------------------------
# GET /api/servers — Listar todos los servidores
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ServerOut])
async def list_servers(db: AsyncSession = Depends(get_db)):
    """
    Devuelve la lista completa de servidores ordenados por nombre.
    Se incluyen tanto los activos como los desactivados.
    """
    result = await db.execute(select(Server).order_by(Server.name))
    return result.scalars().all()


# ---------------------------------------------------------------------------
# POST /api/servers — Crear servidor
# ---------------------------------------------------------------------------

@router.post("/", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
async def create_server(payload: ServerCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo servidor en la base de datos.
    Si el servidor queda activo, ejecuta una comprobacion inicial para
    evitar que arranque en estado desconocido.
    """
    server = Server(**payload.model_dump())
    db.add(server)
    await db.flush()

    if server.is_active:
        await check_server(server, db, send_alerts=False)

    await db.refresh(server)
    return server


# ---------------------------------------------------------------------------
# GET /api/servers/{id} — Obtener servidor por ID
# ---------------------------------------------------------------------------

@router.get("/{server_id}", response_model=ServerOut)
async def get_server(server_id: int, db: AsyncSession = Depends(get_db)):
    """Devuelve los datos de un servidor específico."""
    server = await _get_server_or_404(server_id, db)
    return server


# ---------------------------------------------------------------------------
# PUT /api/servers/{id} — Actualizar servidor
# ---------------------------------------------------------------------------

@router.put("/{server_id}", response_model=ServerOut)
async def update_server(
    server_id: int,
    payload: ServerUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza los campos del servidor indicados en el payload.
    Los campos no incluidos en el payload no se modifican.
    """
    server = await _get_server_or_404(server_id, db)
    previous_is_active = server.is_active

    # Actualizamos solo los campos que vienen en el payload (PATCH semántico)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)

    await db.flush()

    should_run_initial_check = server.is_active and (
        not previous_is_active or "ip_address" in update_data
    )
    if should_run_initial_check:
        await check_server(server, db, send_alerts=False)

    await db.refresh(server)
    return server


# ---------------------------------------------------------------------------
# DELETE /api/servers/{id} — Eliminar servidor
# ---------------------------------------------------------------------------

@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(server_id: int, db: AsyncSession = Depends(get_db)):
    """
    Elimina un servidor y todos sus logs de comprobación asociados
    (cascade configurado en el modelo).
    """
    server = await _get_server_or_404(server_id, db)
    await db.delete(server)


# ---------------------------------------------------------------------------
# POST /api/servers/{id}/ping — Ping manual inmediato
# ---------------------------------------------------------------------------

@router.post("/{server_id}/ping", response_model=ManualPingOut)
async def manual_ping(
    server_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Lanza una comprobacion inmediata, persiste estado y log,
    pero no dispara correos de alerta.
    """
    server = await _get_server_or_404(server_id, db)
    result = await check_server(server, db, send_alerts=False)
    await db.refresh(server)

    return {
        "server_id": server_id,
        "server_name": server.name,
        "ip_address": server.ip_address,
        "success": result.status == "up",
        "last_status": server.last_status,
        "response_ms": result.response_ms,
        "error": result.error_message,
        "checked_at": result.checked_at,
    }


# ---------------------------------------------------------------------------
# Helper privado
# ---------------------------------------------------------------------------

async def _get_server_or_404(server_id: int, db: AsyncSession) -> Server:
    """
    Devuelve el servidor con el ID dado o lanza HTTP 404 si no existe.
    Responsabilidad única: búsqueda de servidor con manejo de error.
    """
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Servidor con id={server_id} no encontrado",
        )
    return server
