from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_citizen
from app.models.citizen import Citizen, CitizenAddress, CitizenEducation, CitizenFamilyMember, CitizenWorkExperience, CitizenLanguage, CitizenPhysicalStandard
from app.schemas.citizen import (
    CitizenProfileResponse, AddressCreate, AddressResponse,
    EducationCreate, EducationResponse, FamilyMemberCreate, FamilyMemberResponse,
    WorkExperienceCreate, WorkExperienceResponse, LanguageCreate, LanguageResponse,
    PhysicalStandardCreate, PhysicalStandardResponse
)

router = APIRouter(prefix="/citizens", tags=["Citizen Profiles"])

@router.get("/me", response_model=CitizenProfileResponse)
async def get_my_profile(
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current logged in citizen's full profile details.
    """
    # Eager load relationships to match Pydantic schemas
    stmt = (
        select(Citizen)
        .where(Citizen.citizen_id == citizen.citizen_id)
        .options(
            selectinload(Citizen.addresses),
            selectinload(Citizen.education),
            selectinload(Citizen.family_members),
            selectinload(Citizen.work_experience),
            selectinload(Citizen.languages),
            selectinload(Citizen.physical_standard)
        )
    )
    res = await db.execute(stmt)
    full_citizen = res.scalar_one()
    return full_citizen

@router.post("/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def add_address(
    request: AddressCreate,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new address record to citizen profile.
    """
    # If primary, reset other primary addresses of this citizen
    if request.is_primary:
        from sqlalchemy import update
        await db.execute(
            update(CitizenAddress)
            .where(CitizenAddress.citizen_id == citizen.citizen_id)
            .values(is_primary=False)
        )

    new_address = CitizenAddress(
        citizen_id=citizen.citizen_id,
        **request.model_dump()
    )
    db.add(new_address)
    await db.commit()
    await db.refresh(new_address)
    return new_address

@router.post("/me/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
async def add_education(
    request: EducationCreate,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Add educational qualifications to profile.
    """
    new_edu = CitizenEducation(
        citizen_id=citizen.citizen_id,
        **request.model_dump()
    )
    db.add(new_edu)
    await db.commit()
    await db.refresh(new_edu)
    return new_edu

@router.post("/me/family", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_family_member(
    request: FamilyMemberCreate,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a family member detail.
    """
    new_fam = CitizenFamilyMember(
        citizen_id=citizen.citizen_id,
        **request.model_dump()
    )
    db.add(new_fam)
    await db.commit()
    await db.refresh(new_fam)
    return new_fam

@router.post("/me/experience", response_model=WorkExperienceResponse, status_code=status.HTTP_201_CREATED)
async def add_experience(
    request: WorkExperienceCreate,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Add work experience blocks.
    """
    new_exp = CitizenWorkExperience(
        citizen_id=citizen.citizen_id,
        **request.model_dump()
    )
    db.add(new_exp)
    await db.commit()
    await db.refresh(new_exp)
    return new_exp

@router.post("/me/physical-standards", response_model=PhysicalStandardResponse, status_code=status.HTTP_201_CREATED)
async def set_physical_standards(
    request: PhysicalStandardCreate,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Configure or update physical metrics.
    """
    # Check if standards exist
    stmt = select(CitizenPhysicalStandard).where(CitizenPhysicalStandard.citizen_id == citizen.citizen_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        for key, value in request.model_dump().items():
            setattr(existing, key, value)
        existing.recorded_at = datetime.utcnow()
        db.add(existing)
        new_standard = existing
    else:
        new_standard = CitizenPhysicalStandard(
            citizen_id=citizen.citizen_id,
            **request.model_dump()
        )
        db.add(new_standard)

    await db.commit()
    await db.refresh(new_standard)
    return new_standard
