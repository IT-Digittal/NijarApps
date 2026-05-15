"""Configuración de SQLAlchemy async para PostgreSQL/PostGIS."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from nijar_dti.config import get_settings

settings = get_settings()

engine = create_async_engine(
    str(settings.database_url),
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(MappedAsDataclass, DeclarativeBase):
    """Clase base para todos los modelos ORM.

    Usa el estilo dataclass de SQLAlchemy 2.0 para tipado estricto y serialización.
    """


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI que provee una sesión de BBDD por request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
