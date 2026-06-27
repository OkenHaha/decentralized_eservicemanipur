from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.admin import Role

async def seed_roles(db: AsyncSession):
    roles = [
        {
            "role_code": "REVENUE_LAMBU",
            "role_name": "Revenue Lambu (Field Inspector)",
            "department": "REVENUE",
            "authority_level": 1,
            "permissions": ["view_assigned", "submit_verification_report"]
        },
        {
            "role_code": "MANDAL",
            "role_name": "Mandal (Circle Reviewer)",
            "department": "REVENUE",
            "authority_level": 2,
            "permissions": ["view_assigned", "review_report", "forward_application"]
        },
        {
            "role_code": "SDC",
            "role_name": "Sub-Deputy Collector",
            "department": "REVENUE",
            "authority_level": 3,
            "permissions": ["view_assigned", "review_report", "approve_application", "reject_application"]
        },
        {
            "role_code": "SDO",
            "role_name": "Sub-Divisional Officer",
            "department": "REVENUE",
            "authority_level": 4,
            "permissions": ["view_assigned", "approve_application", "reject_application", "issue_certificate"]
        },
        {
            "role_code": "EMP_EXCHANGE_OFFICER",
            "role_name": "Employment Exchange Officer",
            "department": "EMPLOYMENT",
            "authority_level": 3,
            "permissions": ["view_assigned", "verify_registration", "renew_registration", "mutate_registration"]
        },
        {
            "role_code": "ADMIN",
            "role_name": "System Administrator",
            "department": "ADMIN",
            "authority_level": 10,
            "permissions": ["manage_users", "manage_offices", "view_audit_logs"]
        }
    ]

    for role_data in roles:
        # Check if already exists
        stmt = select(Role).where(Role.role_code == role_data["role_code"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            new_role = Role(**role_data)
            db.add(new_role)
            print(f"Seeding role: {role_data['role_code']}")
            
    await db.commit()
