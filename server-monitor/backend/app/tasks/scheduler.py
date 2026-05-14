"""
=============================================================
app/tasks/scheduler.py — Scheduler de monitorización periódica

Responsabilidad: ejecutar rondas de comprobación a todos los
servidores activos con un intervalo configurable en tiempo real.

El intervalo se puede modificar desde el endpoint de ajustes sin
reiniciar la aplicación, dado que el scheduler lee el valor en cada
ciclo desde la base de datos de configuración.
=============================================================
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import Server
from app.services.monitor_service import check_server


logger = logging.getLogger(__name__)


class MonitorScheduler:
    """
    Scheduler asíncrono que lanza rondas de ping en bucle.

    El intervalo entre rondas (interval_seconds) es mutable:
    puede cambiarse en tiempo real actualizando el atributo
    desde el exterior (por ejemplo, desde el endpoint /api/settings).
    """

    def __init__(self, interval_seconds: int = 60) -> None:
        """
        Parámetros:
            interval_seconds — Segundos entre rondas de comprobación.
                               Mínimo recomendado: 10 s.
        """
        self.interval_seconds: int = interval_seconds
        self._running: bool = False
        self._last_run_at: datetime | None = None

    # ---------------------------------------------------------------------------
    # Ciclo principal
    # ---------------------------------------------------------------------------

    async def run(self) -> None:
        """
        Bucle principal del scheduler.
        Ejecuta una ronda de comprobación y luego espera 'interval_seconds'.
        Continúa hasta que se llame a stop().
        """
        self._running = True
        logger.info(
            "Scheduler iniciado. Intervalo: %d segundos.", self.interval_seconds
        )

        while self._running:
            await self._run_check_round()
            # Esperamos en pequeños intervalos para que stop() sea rápido
            await self._interruptible_sleep(self.interval_seconds)

        logger.info("Scheduler detenido.")

    def stop(self) -> None:
        """Señaliza al bucle principal que debe detenerse."""
        self._running = False

    # ---------------------------------------------------------------------------
    # Ronda de comprobación
    # ---------------------------------------------------------------------------

    async def _run_check_round(self) -> None:
        """
        Obtiene todos los servidores activos y lanza las comprobaciones
        en paralelo usando asyncio.gather.

        Una ronda fallida (error de BD, excepción inesperada) no detiene
        el scheduler; solo se registra el error en el log.
        """
        self._last_run_at = datetime.now(timezone.utc)
        logger.debug("Iniciando ronda de monitorización: %s", self._last_run_at)

        try:
            async with AsyncSessionLocal() as db:
                # Recuperamos solo los servidores marcados como activos
                servers = await _fetch_active_servers(db)

                if not servers:
                    logger.debug("No hay servidores activos para comprobar.")
                    return

                # Lanzamos todas las comprobaciones en paralelo para reducir
                # el tiempo total de la ronda (especialmente con muchos servidores)
                tasks = [check_server(server, db) for server in servers]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Registramos cualquier excepción individual sin abortar el resto
                for server, result in zip(servers, results):
                    if isinstance(result, Exception):
                        logger.error(
                            "Error al comprobar '%s': %s", server.name, result
                        )

                await db.commit()

        except Exception as exc:
            logger.error("Error en la ronda de monitorización: %s", exc, exc_info=True)

    # ---------------------------------------------------------------------------
    # Helper de espera interrumpible
    # ---------------------------------------------------------------------------

    async def _interruptible_sleep(self, seconds: int) -> None:
        """
        Espera 'seconds' segundos comprobando cada segundo si el scheduler
        debe detenerse. Esto permite que stop() tenga efecto en < 1 s.
        """
        for _ in range(seconds):
            if not self._running:
                break
            await asyncio.sleep(1)


# ---------------------------------------------------------------------------
# Función auxiliar de consulta
# ---------------------------------------------------------------------------

async def _fetch_active_servers(db) -> list[Server]:
    """
    Consulta la BD y devuelve la lista de servidores con is_active = True.
    Responsabilidad única: consulta de servidores activos.
    """
    result = await db.execute(select(Server).where(Server.is_active.is_(True)))
    return list(result.scalars().all())
