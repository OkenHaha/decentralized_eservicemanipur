import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Date, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class VerificationReport(Base):
    __tablename__ = "verification_reports"

    report_id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applications.application_id"), nullable=False, unique=True)
    verifier_id = Column(String(36), ForeignKey("government_officials.official_id"), nullable=False)
    verification_type = Column(String(50), default="FIELD_VISIT")  # FIELD_VISIT, DOCUMENT_CHECK
    verdict = Column(String(20), nullable=False)  # VALID, INVALID
    findings = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    verification_date = Column(Date, nullable=False)
    visit_location = Column(String(255), nullable=True)
    checklist_responses = Column(JSON, nullable=True)
    documents_hash_at_verification = Column(String(64), nullable=False)
    hash_match = Column(Boolean, default=True)
    photo_evidence_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="verification_report")
    verifier = relationship("GovernmentOfficial", back_populates="verification_reports")

class IssuedCertificate(Base):
    __tablename__ = "issued_certificates"

    certificate_id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applications.application_id"), nullable=False, unique=True)
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False)
    issued_by = Column(String(36), nullable=False)  # SDO/SDC official_id
    certificate_number = Column(String(100), unique=True, nullable=False, index=True)
    certificate_type = Column(String(50), nullable=False)  # OBC, SC, ST, PRC, DOMICILE, INCOME
    certificate_hash = Column(String(64), nullable=False)  # SHA-256 hash of PDF or content
    qr_code_hash = Column(String(64), nullable=False)
    qr_code_image_url = Column(String(255), nullable=True)
    certificate_pdf_url = Column(String(255), nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)  # Null if permanent
    is_revoked = Column(Boolean, default=False)
    revocation_reason = Column(String(255), nullable=True)
    issued_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    application = relationship("Application", back_populates="issued_certificate")
