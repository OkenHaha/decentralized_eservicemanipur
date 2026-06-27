from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt
from app.models.admin import GovernmentOfficial, Office, Role

async def seed_officials(db: AsyncSession):
    # Check if officials seeded
    result = await db.execute(select(GovernmentOfficial))
    if result.scalars().first():
        print("Officials already seeded.")
        return

    # Retrieve office SDO-IW
    res = await db.execute(select(Office).where(Office.office_code == "SDO-IW"))
    sdo_office = res.scalar_one_or_none()
    
    # Retrieve office EMP-EX-IW
    res = await db.execute(select(Office).where(Office.office_code == "EMP-EX-IW"))
    emp_office = res.scalar_one_or_none()

    if not sdo_office or not emp_office:
        print("Required offices not found for seeding officials. Seed offices first.")
        return

    # Retrieve roles
    res = await db.execute(select(Role).where(Role.role_code == "REVENUE_LAMBU"))
    lambu_role = res.scalar_one_or_none()
    
    res = await db.execute(select(Role).where(Role.role_code == "SDO"))
    sdo_role = res.scalar_one_or_none()

    res = await db.execute(select(Role).where(Role.role_code == "SDC"))
    sdc_role = res.scalar_one_or_none()

    res = await db.execute(select(Role).where(Role.role_code == "EMP_EXCHANGE_OFFICER"))
    emp_role = res.scalar_one_or_none()

    password_hash = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    officials = [
        {
            "official_id": "lambu-imphal-west",
            "office_id": sdo_office.office_id,
            "role_id": lambu_role.role_id,
            "full_name": "Laishram Sanjit Singh",
            "employee_id": "EMP-LAMBU-001",
            "designation": "REVENUE_LAMBU",
            "phone": "9876543220",
            "email": "sanjit.lambu@manipur.gov.in",
            "blockchain_wallet_address": "0xLAMBU_KEY_IMPHAL_WEST",
            "dsc_serial_number": "DSC-88371-LAMBU",
            "password_hash": password_hash
        },
        {
            "official_id": "sdo-imphal-west",
            "office_id": sdo_office.office_id,
            "role_id": sdo_role.role_id,
            "full_name": "Dr. Ningombam Premjit Singh",
            "employee_id": "EMP-SDO-001",
            "designation": "SDO",
            "phone": "9876543221",
            "email": "premjit.sdo@manipur.gov.in",
            "blockchain_wallet_address": "0xSDO_KEY_IMPHAL_WEST",
            "dsc_serial_number": "DSC-99281-SDO",
            "password_hash": password_hash
        },
        {
            "official_id": "sdc-lamphel",
            "office_id": sdo_office.office_id,
            "role_id": sdc_role.role_id,
            "full_name": "Keisham Ramesh Singh",
            "employee_id": "EMP-SDC-001",
            "designation": "SDC",
            "phone": "9876543222",
            "email": "ramesh.sdc@manipur.gov.in",
            "blockchain_wallet_address": "0xSDC_KEY_LAMPHEL",
            "dsc_serial_number": "DSC-77261-SDC",
            "password_hash": password_hash
        },
        {
            "official_id": "emp-officer-iw",
            "office_id": emp_office.office_id,
            "role_id": emp_role.role_id,
            "full_name": "Khumanthem Diana Devi",
            "employee_id": "EMP-EXCH-001",
            "designation": "EMP_EXCHANGE_OFFICER",
            "phone": "9876543223",
            "email": "diana.emp@manipur.gov.in",
            "blockchain_wallet_address": "0xEMP_OFFICER_KEY_IMPHAL_WEST",
            "dsc_serial_number": "DSC-55123-EMP",
            "password_hash": password_hash
        }
    ]

    for official_data in officials:
        new_official = GovernmentOfficial(**official_data)
        db.add(new_official)
        print(f"Seeding official: {official_data['full_name']} ({official_data['designation']})")

    await db.commit()
