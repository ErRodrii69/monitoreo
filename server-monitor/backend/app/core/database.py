"""
=============================================================
app/core/database.py — Conexión asíncrona a PostgreSQL

Configura SQLAlchemy con el driver asyncpg para que todas las
operaciones de BD sean no bloqueantes dentro del event loop de
FastAPI/asyncio.
=============================================================
"""

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


# ---------------------------------------------------------------------------
# Motor y sesión
# ---------------------------------------------------------------------------

_settings = get_settings()
_database_url = make_url(_settings.database_url)

engine_kwargs = {
    "echo": False,
}

if _database_url.get_backend_name() != "sqlite":
    engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
        }
    )

engine = create_async_engine(
    _settings.database_url,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Base declarativa compartida por todos los modelos
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos ORM del proyecto."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def create_tables() -> None:
    """
    Crea todas las tablas definidas en los modelos si no existen.
    Se llama una sola vez durante el startup de la aplicación.
    """
    # Importamos los modelos aquí para que estén registrados en Base.metadata
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """
    Dependencia de FastAPI que provee una sesión de BD por petición.
    Garantiza que la sesión se cierra correctamente al terminar.

    Uso en un router:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
