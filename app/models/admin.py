import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Utility function for UUID primary keys compatible with SQLite
def generate_uuid():
    return str(uuid.uuid4())

class Office(Base):
    __tablename__ = "offices"

    office_id = Column(String(36), primary_key=True, default=generate_uuid)
    office_code = Column(String(50), unique=True, nullable=False, index=True)
    office_name = Column(String(100), nullable=False)
    office_type = Column(String(50), nullable=False)  # DC_OFFICE, SDO_OFFICE, CIRCLE_OFFICE, EMPLOYMENT_EXCHANGE
    district = Column(String(100), nullable=False)
    sub_division = Column(String(100), nullable=True)
    full_address = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    parent_office_id = Column(String(36), ForeignKey("offices.office_id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent_office = relationship("Office", remote_side=[office_id], backref="child_offices")
    officials = relationship("GovernmentOfficial", back_populates="office")
    applications = relationship("Application", back_populates="office")

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(String(36), primary_key=True, default=generate_uuid)
    role_code = Column(String(50), unique=True, nullable=False, index=True)  # REVENUE_LAMBU, MANDAL, SDO, SDC, DC, ADMIN, EMP_EXCHANGE_OFFICER
    role_name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)  # REVENUE, EMPLOYMENT, ADMIN
    authority_level = Column(Integer, nullable=False)
    permissions = Column(JSON, nullable=True)  # List of allowed actions
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    officials = relationship("GovernmentOfficial", back_populates="role")

class GovernmentOfficial(Base):
    __tablename__ = "government_officials"

    official_id = Column(String(36), primary_key=True, default=generate_uuid)
    office_id = Column(String(36), ForeignKey("offices.office_id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.role_id"), nullable=False)
    full_name = Column(String(100), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    designation = Column(String(100), nullable=False)  # Lambu, SDO, SDC, etc.
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    blockchain_wallet_address = Column(String(100), unique=True, nullable=False, index=True)
    dsc_serial_number = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    password_hash = Column(String(255), nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    office = relationship("Office", back_populates="officials")
    role = relationship("Role", back_populates="officials")
    verification_reports = relationship("VerificationReport", back_populates="verifier")
    remarks = relationship("ApplicationRemark", back_populates="official")

class ServiceCatalog(Base):
    __tablename__ = "service_catalog"

    service_id = Column(String(36), primary_key=True, default=generate_uuid)
    service_code = Column(String(50), unique=True, nullable=False, index=True)  # OBC_CERT, SC_CERT, INCOME_CERT, etc.
    service_name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)  # REVENUE, EMPLOYMENT_EXCHANGE, etc.
    description = Column(String(255), nullable=True)
    required_fields_schema = Column(JSON, nullable=False)  # JSON Schema for application fields
    required_documents_schema = Column(JSON, nullable=False)  # JSON Schema for document types
    max_file_size_kb = Column(Integer, default=200)
    fee_amount = Column(Numeric(10, 2), default=0.00)
    expected_processing_days = Column(Integer, default=15)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applications = relationship("Application", back_populates="service")
    workflow_stages = relationship("WorkflowStage", back_populates="service")

class WorkflowStage(Base):
    __tablename__ = "workflow_stages"

    stage_id = Column(String(36), primary_key=True, default=generate_uuid)
    service_id = Column(String(36), ForeignKey("service_catalog.service_id"), nullable=False)
    stage_order = Column(Integer, nullable=False)
    stage_code = Column(String(50), nullable=False)  # SUBMITTED, LAMBU_REVIEW, MANDAL_REVIEW, SDO_APPROVAL, etc.
    stage_name = Column(String(100), nullable=False)
    required_role = Column(String(50), nullable=False)  # Role code required to act
    sla_hours = Column(Integer, default=48)
    is_terminal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    service = relationship("ServiceCatalog", back_populates="workflow_stages")
