from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.admin import Office

async def seed_offices(db: AsyncSession):
    # Check if offices are already seeded
    result = await db.execute(select(Office))
    if result.scalars().first():
        print("Offices already seeded.")
        return

    # Seed top-level DC Office
    dc_office = Office(
        office_code="DC-IW",
        office_name="DC Office Imphal West",
        office_type="DC_OFFICE",
        district="Imphal West",
        full_address="Babupara, Imphal, Manipur",
        phone="0385-2450123",
        email="dc-imphalwest@manipur.gov.in"
    )
    db.add(dc_office)
    await db.flush()  # to get dc_office.office_id
    
    # SDO Office Lamphel under DC-IW
    sdo_lamphel = Office(
        office_code="SDO-IW",
        office_name="SDO Office Lamphel",
        office_type="SDO_OFFICE",
        district="Imphal West",
        sub_division="Lamphelpat",
        full_address="Lamphelpat, Imphal, Manipur",
        phone="0385-2450124",
        email="sdo-lamphel@manipur.gov.in",
        parent_office_id=dc_office.office_id
    )
    db.add(sdo_lamphel)
    
    # Employment Exchange Office
    emp_office = Office(
        office_code="EMP-EX-IW",
        office_name="District Employment Exchange Imphal West",
        office_type="EMPLOYMENT_EXCHANGE",
        district="Imphal West",
        full_address="Lamphelpat near SDO, Imphal, Manipur",
        phone="0385-2450125",
        email="emp-imphalwest@manipur.gov.in",
        parent_office_id=dc_office.office_id
    )
    db.add(emp_office)
    
    print("Seeding offices hierarchy complete.")
    await db.commit()
