from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.router import api_router
from app.database import engine, SessionLocal
from app.seed.seed_roles import seed_roles
from app.seed.seed_offices import seed_offices
from app.seed.seed_services import seed_services
from app.seed.seed_officials import seed_officials
from app.seed.seed_citizens import seed_citizens

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Auto-seed database if empty
    print("FastAPI starting up. Running database seeds if required...")
    async with SessionLocal() as db:
        try:
            await seed_roles(db)
            await seed_offices(db)
            await seed_services(db)
            await seed_officials(db)
            await seed_citizens(db)
        except Exception as e:
            print(f"Error during startup seeding: {e}")
            # Don't crash app if seed fails, but log it
        finally:
            await db.close()
            
    yield
    
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A hybrid database-ledger replica implementation of Manipur's anti-corruption e-Services Manipur portal.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include master API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "message": "Welcome to e-Services Manipur Anti-Corruption Platform API",
        "docs_url": "/docs"
    }
