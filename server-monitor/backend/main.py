"""
=============================================================
SISTEMA DE MONITORIZACIÓN DE SERVIDORES
main.py — Punto de entrada de la aplicación FastAPI

Configura la app, registra los routers, gestiona el ciclo de
vida (startup / shutdown) e inicia el scheduler de monitorización.
=============================================================
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import servers, checks, settings as settings_router
from app.core.database import create_tables
from app.core.config import get_settings
from app.tasks.scheduler import MonitorScheduler


# ---------------------------------------------------------------------------
# Ciclo de vida de la aplicación
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el arranque y el cierre limpio de la aplicación.
    Al iniciar:  crea las tablas en BD y arranca el scheduler.
    Al cerrar:   detiene el scheduler de forma ordenada.
    """
    # --- STARTUP ---
    await create_tables()

    cfg = get_settings()
    scheduler = MonitorScheduler(interval_seconds=cfg.check_interval_seconds)
    app.state.scheduler = scheduler
    asyncio.create_task(scheduler.run())

    yield  # La app está corriendo aquí

    # --- SHUTDOWN ---
    scheduler.stop()


# ---------------------------------------------------------------------------
# Creación de la app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Server Monitor API",
    description="API REST para monitorización de servidores mediante ICMP ping.",
    version="1.0.0",
    lifespan=lifespan,
)

# Permitimos peticiones desde el frontend (mismo origen en producción,
# pero se puede ampliar para desarrollo local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers de la API
# ---------------------------------------------------------------------------

app.include_router(servers.router,  prefix="/api/servers",  tags=["servers"])
app.include_router(checks.router,   prefix="/api/checks",   tags=["checks"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])

# ---------------------------------------------------------------------------
# Ficheros estáticos + SPA fallback
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Sirve el index.html del frontend para cualquier ruta no-API."""
    return FileResponse("../frontend/templates/index.html")
