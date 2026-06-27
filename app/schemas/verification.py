from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Dict, Any

class VerificationSubmit(BaseModel):
    verdict: str  # VALID | INVALID
    findings: str
    lambu_signature_token: str
    recommendation: Optional[str] = None
    visit_location: Optional[str] = None
    checklist_responses: Optional[Dict[str, Any]] = None

class AuthorizationSubmit(BaseModel):
    decision: str  # ISSUE | DENY
    sdo_signature_token: str

class VerificationReportResponse(BaseModel):
    report_id: str
    application_id: str
    verifier_id: str
    verification_type: str
    verdict: str
    findings: str
    recommendation: Optional[str] = None
    verification_date: date
    visit_location: Optional[str] = None
    hash_match: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CertificateResponse(BaseModel):
    certificate_id: str
    application_id: str
    citizen_id: str
    issued_by: str
    certificate_number: str
    certificate_type: str
    certificate_hash: str
    qr_code_hash: str
    qr_code_image_url: Optional[str] = None
    certificate_pdf_url: Optional[str] = None
    valid_from: date
    valid_until: Optional[date] = None
    issued_at: datetime

    class Config:
        from_attributes = True
