from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.dependencies import get_current_official
from app.models.admin import GovernmentOfficial, Role
from app.models.application import Application, ApplicationRemark
from app.schemas.admin import RemarkCreate, RemarkResponse
from app.schemas.application import ApplicationResponse

router = APIRouter(prefix="/admin", tags=["Officer Operations"])

@router.get("/queue", response_model=List[ApplicationResponse])
async def get_assigned_queue(
    official: GovernmentOfficial = Depends(get_current_official),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the application queue for the logged-in official.
    - Lambu gets all SUBMITTED applications for field verification.
    - SDO/SDC gets all FIELD_VERIFIED applications for approval/rejection.
    """
    stmt_role = select(Role).where(Role.role_id == official.role_id)
    res_role = await db.execute(stmt_role)
    role = res_role.scalar_one()

    # Filter based on role status pipeline
    if role.role_code == "REVENUE_LAMBU":
        status_filter = ["SUBMITTED"]
    elif role.role_code in ["SDO", "SDC"]:
        status_filter = ["FIELD_VERIFIED"]
    else:
        status_filter = []

    stmt = (
        select(Application)
        .where(
            Application.processing_office_id == official.office_id,
            Application.current_status.in_(status_filter)
        )
        .options(selectinload(Application.documents))
        .order_by(Application.submitted_at.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/remarks/{application_id}", response_model=RemarkResponse, status_code=status.HTTP_201_CREATED)
async def add_application_remark(
    application_id: str,
    request: RemarkCreate,
    official: GovernmentOfficial = Depends(get_current_official),
    db: AsyncSession = Depends(get_db)
):
    """
    Add administrative remark/query to an application.
    """
    # Verify application exists
    stmt_app = select(Application).where(Application.application_id == application_id)
    res_app = await db.execute(stmt_app)
    app = res_app.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    new_remark = ApplicationRemark(
        application_id=application_id,
        official_id=official.official_id,
        **request.model_dump()
    )
    db.add(new_remark)
    
    # If a query requires citizen response, update status to RETURNED
    if request.requires_citizen_response:
        app.current_status = "RETURNED"
        app.return_reason = request.remark_text
        db.add(app)

    await db.commit()
    await db.refresh(new_remark)
    return new_remark
