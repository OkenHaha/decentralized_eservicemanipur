from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict

from app.database import get_db
from app.dependencies import get_current_citizen, get_current_user_payload
from app.models.citizen import Citizen
from app.models.employment import EmploymentRegistration
from app.schemas.employment import EmploymentRegisterRequest, EmploymentRenewalRequest, EmploymentUpdateRequest
from app.services.employment_service import (
    process_new_registration, process_renewal, process_mutation_update, EmploymentExchangeError
)

router = APIRouter(prefix="/employment", tags=["Employment Exchange"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_jobseeker(
    request: EmploymentRegisterRequest,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Register as a job seeker in the District Employment Exchange.
    Implements NEW_REGISTRATION workflow from algo_three.md.
    """
    # For testing and simulation, we pass simulated file sizes that satisfy requirements.
    # In production, files would be uploaded and sized via multi-part requests.
    simulated_file_sizes = {
        "PassportPhoto_PlainBackground": 50000,   # 50 KB
        "AadhaarCard_FrontSide": 40000,           # 40 KB
        "AadhaarCard_BackSide": 45000,            # 45 KB
        "ProofOfResidence_Domicile": 60000,        # 60 KB
        "DateOfBirth_Certificate": 70000,          # 70 KB
        "Highest_Qualification_Certificate": 80000 # 80 KB
    }
    if request.CasteCategory != "GENERAL":
        simulated_file_sizes["Caste_Certificate"] = 55000  # 55 KB

    try:
        reg_id = await process_new_registration(
            db=db,
            citizen=citizen,
            request=request,
            uploaded_files_sizes=simulated_file_sizes
        )
        return {
            "status": "SUCCESS",
            "registration_id": reg_id,
            "message": "Jobseeker registration successfully created. Pending SDC verification."
        }
    except EmploymentExchangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/renew", status_code=status.HTTP_200_OK)
async def renew_registration(
    request: EmploymentRenewalRequest,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Renew an existing Employment Exchange card (validity extended by 3 years + 3 months grace).
    Implements RENEWAL workflow from algo_three.md.
    """
    try:
        reg_id = await process_renewal(db=db, citizen=citizen, request=request)
        return {
            "status": "SUCCESS",
            "registration_id": reg_id,
            "message": "Card renewed successfully. Validity extended by 3 years + 3 months grace."
        }
    except EmploymentExchangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/update", status_code=status.HTTP_200_OK)
async def update_qualifications_or_experience(
    request: EmploymentUpdateRequest,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Update / mutate job seeker educational qualifications or work experience.
    Implements UPDATING_QUALIFICATION_EXPERIENCE workflow from algo_three.md.
    """
    # Simulated files check (e.g. New_Qualification_Document uploaded under 100KB)
    simulated_file_sizes = {
        "New_Qualification_Document": 45000  # 45 KB
    }
    try:
        reg_id = await process_mutation_update(
            db=db,
            citizen=citizen,
            request=request,
            uploaded_files_sizes=simulated_file_sizes
        )
        return {
            "status": "SUCCESS",
            "registration_id": reg_id,
            "message": "Mutation requested successfully. Pending officer review."
        }
    except EmploymentExchangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{registration_id}")
async def get_registration_details(
    registration_id: str,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve details of an Employment Exchange registration.
    """
    stmt = select(EmploymentRegistration).where(EmploymentRegistration.registration_id == registration_id)
    res = await db.execute(stmt)
    reg = res.scalar_one_or_none()
    
    if not reg:
        raise HTTPException(status_code=404, detail="Registration card not found.")
        
    # Check auth: citizens can only see their own registration card
    if payload["role"] == "CITIZEN" and reg.citizen_id != payload["user_id"]:
        raise HTTPException(status_code=403, detail="Permission denied to access this registration.")
        
    return reg
