import asyncio
import sys
from pathlib import Path

# Add project root to python path to resolve imports correctly
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal, engine
from app.seed.seed_roles import seed_roles
from app.seed.seed_offices import seed_offices
from app.seed.seed_services import seed_services
from app.seed.seed_officials import seed_officials
from app.seed.seed_citizens import seed_citizens

async def main():
    print("Starting database seeding...")
    async with SessionLocal() as db:
        try:
            print("--- Seeding Roles ---")
            await seed_roles(db)
            
            print("--- Seeding Offices ---")
            await seed_offices(db)
            
            print("--- Seeding Services ---")
            await seed_services(db)
            
            print("--- Seeding Officials ---")
            await seed_officials(db)
            
            print("--- Seeding Citizens ---")
            await seed_citizens(db)
            
            print("Database seeding completed successfully.")
        except Exception as e:
            print(f"Error seeding database: {e}")
            raise
        finally:
            await db.close()
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
