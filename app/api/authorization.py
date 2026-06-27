from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_official
from app.models.admin import GovernmentOfficial, Role
from app.models.application import Application
from app.schemas.verification import AuthorizationSubmit, CertificateResponse
from app.services.ledger_service import append_approval_block, get_latest_block, LedgerError
from app.services.certificate_service import mint_digital_certificate

router = APIRouter(prefix="/authorize", tags=["Final Authorization"])

@router.post("/{application_id}", response_model=CertificateResponse)
async def authorize_application(
    application_id: str,
    request: AuthorizationSubmit,
    official: GovernmentOfficial = Depends(get_current_official),
    db: AsyncSession = Depends(get_db)
):
    """
    Final decision step (approve or reject) by SDO/SDC.
    Implements AuthorizeFinalCertificateIssuance from authorizatoin.md.
    Verify signature + link blockchain block + mint final digital certificate with QR code if approved.
    """
    # 1. Fetch official role code to check authority
    stmt_role = select(Role).where(Role.role_id == official.role_id)
    res_role = await db.execute(stmt_role)
    role = res_role.scalar_one()
    
    if role.role_code not in ["SDO", "SDC"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Final authorization must be performed by SDO or SDC."
        )

    # 2. Append approval block to ledger
    try:
        new_block = await append_approval_block(
            db=db,
            application_id=application_id,
            decision=request.decision,
            sdo_signature_token=request.sdo_signature_token
        )
    except LedgerError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 3. Mint digital certificate if approved
    if request.decision == "ISSUE":
        cert = await mint_digital_certificate(
            db=db,
            application_id=application_id,
            sdo_id=official.official_id,
            sdo_signature_token=request.sdo_signature_token,
            file_fingerprint=new_block.aggregate_data_hash
        )
        await db.commit()
        return cert
    else:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Application terminated: Rejected by Authority."
        )
