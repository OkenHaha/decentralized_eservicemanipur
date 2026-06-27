import uuid
from sqlalchemy import Column, String, ForeignKey, Date, DateTime, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class EmploymentRegistration(Base):
    __tablename__ = "employment_registrations"

    registration_id = Column(String(50), primary_key=True)  # Format: MN-EMP-YYYY-XXXXX
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False, unique=True)
    processing_office_id = Column(String(36), ForeignKey("offices.office_id"), nullable=False)
    current_state = Column(String(50), default="PENDING_VERIFICATION")  # PENDING_VERIFICATION, ACTIVE, EXPIRED, etc.
    seniority_date = Column(Date, nullable=False)
    lifespan_expiry_date = Column(Date, nullable=False)
    last_renewal_date = Column(Date, nullable=True)
    renewal_count = Column(Integer, default=0)
    physical_standards_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    citizen = relationship("Citizen", back_populates="employment_registration")
