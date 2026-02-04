"""
========================================
Database Connection
========================================
SQLAlchemy async database setup
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager

from app.config import settings


# ========================================
# Base Model
# ========================================
class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# ========================================
# Engine Setup
# ========================================
# Convert sqlite:/// to sqlite+aiosqlite:///
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite:///"):
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # Check connection health before using
    pool_recycle=300,    # Recycle connections after 5 minutes
    pool_size=5,         # Connection pool size
    max_overflow=10,     # Max extra connections beyond pool_size
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# ========================================
# Session Management
# ========================================
@asynccontextmanager
async def get_db_session():
    """Get database session with automatic cleanup"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db():
    """Dependency for FastAPI endpoints"""
    async with get_db_session() as session:
        yield session


# ========================================
# Initialization
# ========================================
async def init_database():
    """Initialize database and create tables"""
    async with engine.begin() as conn:
        # Import all models to register them
        from app.database.models import (
            Conversation,
            Message,
            Document,
            Insight,
            Report,
            ScheduledTask,
            Customer,
            Product,
            Sale,
            SupportTicket,
            BusinessMetric
        )
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    """Close database connections"""
    await engine.dispose()
