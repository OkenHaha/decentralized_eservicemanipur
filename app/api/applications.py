from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.dependencies import get_current_citizen, get_current_user_payload
from app.models.citizen import Citizen
from app.models.admin import ServiceCatalog
from app.models.application import Application, ApplicationStatusLog
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationStatusLogResponse, ServiceCatalogResponse
from app.services.application_service import validate_and_submit_revenue_application, ApplicationValidationError

router = APIRouter(prefix="/applications", tags=["Applications Management"])

@router.get("/services", response_model=List[ServiceCatalogResponse])
async def list_services(db: AsyncSession = Depends(get_db)):
    """
    List all available services and their requirements in the Service Catalog.
    """
    stmt = select(ServiceCatalog).where(ServiceCatalog.is_active == True)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def submit_application(
    request: ApplicationCreate,
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit application metadata and configuration.
    Initializes application in DRAFT state. Once the required files are uploaded,
    it transitions to SUBMITTED and locks on the ledger.
    """
    try:
        # Create application and record status log
        app = await validate_and_submit_revenue_application(
            db=db,
            citizen=citizen,
            service_code=request.service_code,
            form_payload=request.form_data,
            declaration_accepted=request.declaration_accepted,
            purpose=request.purpose
        )
        
        # Set to DRAFT since documents are needed to finalize
        app.current_status = "DRAFT"
        await db.commit()
        
        # Eager load the application with documents for response serialization
        stmt = (
            select(Application)
            .where(Application.application_id == app.application_id)
            .options(selectinload(Application.documents))
        )
        res = await db.execute(stmt)
        return res.scalar_one()
    except ApplicationValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/mine", response_model=List[ApplicationResponse])
async def get_my_applications(
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all applications submitted by the current citizen.
    """
    stmt = (
        select(Application)
        .where(Application.citizen_id == citizen.citizen_id)
        .options(selectinload(Application.documents))
        .order_by(Application.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve details of a specific application.
    """
    stmt = (
        select(Application)
        .where(Application.application_id == application_id)
        .options(selectinload(Application.documents))
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
        
    # Check authorization: Citizens can only see their own applications
    if payload["role"] == "CITIZEN" and app.citizen_id != payload["user_id"]:
        raise HTTPException(status_code=403, detail="Permission denied to access this application.")
        
    return app

@router.get("/{application_id}/status-history", response_model=List[ApplicationStatusLogResponse])
async def get_status_history(
    application_id: str,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full chronological logs of all status transitions for the application.
    """
    stmt_app = select(Application).where(Application.application_id == application_id)
    res_app = await db.execute(stmt_app)
    app = res_app.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
        
    if payload["role"] == "CITIZEN" and app.citizen_id != payload["user_id"]:
        raise HTTPException(status_code=403, detail="Permission denied to access this application.")

    stmt = (
        select(ApplicationStatusLog)
        .where(ApplicationStatusLog.application_id == application_id)
        .order_by(ApplicationStatusLog.changed_at.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()
