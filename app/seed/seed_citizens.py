import hashlib
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.citizen import Citizen, CitizenAddress

def get_sha256_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

async def seed_citizens(db: AsyncSession):
    # Check if citizens already seeded
    result = await db.execute(select(Citizen))
    if result.scalars().first():
        print("Citizens already seeded.")
        return

    # Seed citizen 1 (Tomba Singh)
    citizen_1 = Citizen(
        citizen_id="citizen-tomba",
        aadhaar_hash=get_sha256_hash("999900000001"),
        full_name="Laishram Tomba Singh",
        father_name="Laishram Ibohal Singh",
        date_of_birth=datetime.date(1995, 3, 15),
        gender="MALE",
        religion="Hinduism",
        caste_category="OBC",
        sub_caste="Meitei",
        phone_primary="9876543210",
        epic_number="MAN/01/012/345678",
        marital_status="SINGLE",
        blood_group="O+"
    )
    db.add(citizen_1)
    await db.flush()

    address_1 = CitizenAddress(
        citizen_id=citizen_1.citizen_id,
        address_type="PERMANENT",
        house_no="42",
        street_locality="Kwakeithel Heinoukhongnembi",
        village_town="Imphal",
        post_office="Imphal SO",
        police_station="Imphal PS",
        circle="Lamphel",
        sub_division="Lamphelpat",
        district="Imphal West",
        pin_code="795001",
        area_type="URBAN",
        is_primary=True
    )
    db.add(address_1)

    # Seed citizen 2 (Bembem Devi)
    citizen_2 = Citizen(
        citizen_id="citizen-bembem",
        aadhaar_hash=get_sha256_hash("999900000002"),
        full_name="Oinam Bembem Devi",
        father_name="Oinam Jugeshwor Singh",
        date_of_birth=datetime.date(1988, 7, 22),
        gender="FEMALE",
        religion="Hinduism",
        caste_category="GENERAL",
        phone_primary="9876543211",
        marital_status="MARRIED",
        blood_group="A+"
    )
    db.add(citizen_2)
    await db.flush()

    address_2 = CitizenAddress(
        citizen_id=citizen_2.citizen_id,
        address_type="PERMANENT",
        house_no="108",
        street_locality="Thoubal Achouba",
        village_town="Thoubal",
        post_office="Thoubal SO",
        police_station="Thoubal PS",
        circle="Thoubal",
        sub_division="Thoubal",
        district="Thoubal",
        pin_code="795138",
        area_type="RURAL",
        is_primary=True
    )
    db.add(address_2)

    print("Seeding test citizens complete.")
    await db.commit()
