import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, JSON, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Application(Base):
    __tablename__ = "applications"

    application_id = Column(String(50), primary_key=True)  # custom format: MN-REV-YYYY-XXXXX
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False)
    service_id = Column(String(36), ForeignKey("service_catalog.service_id"), nullable=False)
    processing_office_id = Column(String(36), ForeignKey("offices.office_id"), nullable=False)
    current_status = Column(String(50), default="SUBMITTED")  # DRAFT, SUBMITTED, UNDER_REVIEW, FIELD_VERIFICATION, etc.
    form_data = Column(JSON, nullable=False)  # Flexibly store form fields
    purpose = Column(String(255), nullable=True)
    declaration_accepted = Column(Boolean, default=False)
    rejection_reason = Column(String(255), nullable=True)
    return_reason = Column(String(255), nullable=True)
    priority_level = Column(Integer, default=0)  # 0=Normal, 1=Urgent, 2=VIP
    submitted_at = Column(DateTime, default=datetime.utcnow)
    last_status_change_at = Column(DateTime, default=datetime.utcnow)
    expected_completion_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    citizen = relationship("Citizen", back_populates="applications")
    service = relationship("ServiceCatalog", back_populates="applications")
    office = relationship("Office", back_populates="applications")
    
    documents = relationship("ApplicationDocument", back_populates="application", cascade="all, delete-orphan")
    status_logs = relationship("ApplicationStatusLog", back_populates="application", cascade="all, delete-orphan")
    fee = relationship("ApplicationFee", back_populates="application", uselist=False, cascade="all, delete-orphan")
    remarks = relationship("ApplicationRemark", back_populates="application", cascade="all, delete-orphan")
    assignments = relationship("ApplicationAssignment", back_populates="application", cascade="all, delete-orphan")
    ledger_entries = relationship("BlockchainLedgerEntry", back_populates="application", cascade="all, delete-orphan")
    issued_certificate = relationship("IssuedCertificate", back_populates="application", uselist=False, cascade="all, delete-orphan")
    verification_report = relationship("VerificationReport", back_populates="application", uselist=False, cascade="all, delete-orphan")

class ApplicationDocument(Base):
    __tablename__ = "application_documents"

    document_id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applications.application_id"), nullable=False)
    document_type = Column(String(100), nullable=False)  # Jamabandi, VoterID, PassportPhoto, etc.
    document_label = Column(String(100), nullable=False)
    original_filename = Column(String(150), nullable=False)
    storage_url = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 fingerprint
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(36), nullable=True)  # ID of GovernmentOfficial (stored as string to avoid schema load complexity)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    application = relationship("Application", back_populates="documents")

class ApplicationStatusLog(Base):
    __tablename__ = "application_status_logs"

    log_id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applications.application_id"), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_by = Column(String(36), nullable=False)  # citizen_id or official_id
    changed_by_role = Column(String(50), nullable=False)  # CITIZEN, LAMBU, SDO, SDC, etc.
    remarks = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True)  # IP address, client device etc.
    changed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="status_logs")

class ApplicationFee(Base):
    __tablename__ = "application_fees"

    fee_id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applications.application_id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # UPI, NET_BANKING, cash, waived
    transaction_reference = Column(String(100), nullable=True)
    payment_status = Column(String(50), default="PENDING")  # PENDING, COMPLETED, FAILED, waived
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="fee")

class ApplicationRemark(Base):
    __tablename__ = "application_remarks"

    remark_id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applications.application_id"), nullable=False)
    official_id = Column(String(36), ForeignKey("government_officials.official_id"), nullable=False)
    remark_type = Column(String(50), nullable=False)  # OBSERVATION, QUERY, OBJECTION, INTERNAL_NOTE
    remark_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)  # True = hidden from citizen
    requires_citizen_response = Column(Boolean, default=False)
    citizen_response = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="remarks")
    official = relationship("GovernmentOfficial", back_populates="remarks")

class ApplicationAssignment(Base):
    __tablename__ = "application_assignments"

    assignment_id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(50), ForeignKey("applications.application_id"), nullable=False)
    assigned_to = Column(String(36), nullable=False)  # official_id
    assigned_by = Column(String(36), nullable=False)  # official_id or system
    assignment_type = Column(String(50), default="AUTO")  # AUTO, MANUAL, REASSIGNMENT
    assignment_status = Column(String(50), default="ACTIVE")  # ACTIVE, COMPLETED, REASSIGNED
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # Relationships
    application = relationship("Application", back_populates="assignments")
