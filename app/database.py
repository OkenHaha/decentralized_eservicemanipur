from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine for SQLite (using aiosqlite)
# connect_args={"check_same_thread": False} is required for SQLite in multi-threaded contexts like FastAPI
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Async session maker
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Declarative base for models
Base = declarative_base()

# Database session dependency
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
