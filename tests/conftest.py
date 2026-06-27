import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db
from app.main import app
from app.seed.seed_roles import seed_roles
from app.seed.seed_offices import seed_offices
from app.seed.seed_services import seed_services
from app.seed.seed_officials import seed_officials
from app.seed.seed_citizens import seed_citizens

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    Session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with Session() as session:
        # Seed test database
        await seed_roles(session)
        await seed_offices(session)
        await seed_services(session)
        await seed_officials(session)
        await seed_citizens(session)
        
        yield session
        await session.close()
        
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override get_db dependency to use the test session
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()
