from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import datetime

from app.database import get_db
from app.dependencies import get_current_official
from app.models.admin import GovernmentOfficial, Role
from app.models.application import Application, ApplicationDocument, ApplicationStatusLog
from app.models.certificate import VerificationReport
from app.schemas.verification import VerificationSubmit, VerificationReportResponse
from app.services.crypto_service import compute_document_fingerprint
from app.services.ledger_service import append_verification_block, LedgerError

router = APIRouter(prefix="/verify", tags=["Field Verification"])

@router.post("/{application_id}", response_model=VerificationReportResponse)
async def submit_field_verification(
    application_id: str,
    request: VerificationSubmit,
    official: GovernmentOfficial = Depends(get_current_official),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a field verification report for an application.
    Implements ProcessLambuFieldVerification from verification_transaction.md.
    Verify signature + document tampering + append verification block to the immutable ledger.
    """
    # 1. Fetch official role code to check authority
    stmt_role = select(Role).where(Role.role_id == official.role_id)
    res_role = await db.execute(stmt_role)
    role = res_role.scalar_one()
    
    if role.role_code != "REVENUE_LAMBU":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Verification reports must be submitted by a Revenue Lambu."
        )

    # 2. Retrieve application documents to compute current hash fingerprint
    stmt_docs = select(ApplicationDocument).where(ApplicationDocument.application_id == application_id)
    res_docs = await db.execute(stmt_docs)
    docs = res_docs.scalars().all()
    
    if not docs:
        raise HTTPException(
            status_code=400,
            detail="Cannot verify application: No documents have been uploaded."
        )

    # Load file contents to compute aggregate document fingerprint
    files_map = {}
    for d in docs:
        try:
            with open(d.storage_url, "rb") as f:
                files_map[d.document_type] = f.read()
        except FileNotFoundError:
            raise HTTPException(
                status_code=500,
                detail=f"Verification failed: document {d.document_type} file not found on disk."
            )

    current_docs_hash = compute_document_fingerprint(files_map)

    # 3. Call ledger verification function (appends to ledger, verifies signature, catches tampering)
    try:
        new_block = await append_verification_block(
            db=db,
            application_id=application_id,
            verdict=request.verdict,
            lambu_signature_token=request.lambu_signature_token,
            current_docs_hash=current_docs_hash
        )
    except LedgerError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 4. Save detailed VerificationReport entry in database
    report = VerificationReport(
        application_id=application_id,
        verifier_id=official.official_id,
        verification_type="FIELD_VISIT",
        verdict=request.verdict,
        findings=request.findings,
        recommendation=request.recommendation,
        verification_date=datetime.date.today(),
        visit_location=request.visit_location,
        checklist_responses=request.checklist_responses,
        documents_hash_at_verification=current_docs_hash,
        hash_match=True
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report

@router.get("/{application_id}/report", response_model=VerificationReportResponse)
async def get_verification_report(
    application_id: str,
    official: GovernmentOfficial = Depends(get_current_official),
    db: AsyncSession = Depends(get_db)
):
    """
    Get verification report for an application.
    """
    stmt = select(VerificationReport).where(VerificationReport.application_id == application_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Verification report not found.")
        
    return report
