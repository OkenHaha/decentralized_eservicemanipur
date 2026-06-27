from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ledger_service import traverse_audit_trail, verify_ledger_integrity

router = APIRouter(prefix="/audit", tags=["Public Audit Trail"])

@router.get("/{application_id}")
async def get_public_audit_trail(
    application_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public transparency audit endpoint.
    Implements PublicTransparencyAudit from public_audit.md.
    No authentication required. Returns chronological checkpoint logs from submission to issuance.
    """
    trail = await traverse_audit_trail(db, application_id)
    if not trail:
        raise HTTPException(
            status_code=404, 
            detail="No ledger entries found for this application ID."
        )
    return trail

@router.get("/{application_id}/verify-integrity")
async def verify_ledger_chain_integrity(
    application_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Cryptographically verify the integrity of the ledger chain for a given application.
    Re-computes all SHA-256 hashes sequentially to verify that no tampering has occurred.
    """
    is_intact = await verify_ledger_integrity(db, application_id)
    return {
        "application_id": application_id,
        "is_integrity_intact": is_intact,
        "status": "SECURE" if is_intact else "TAMPERED_WARNING"
    }
