import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, Date, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Citizen(Base):
    __tablename__ = "citizens"

    citizen_id = Column(String(36), primary_key=True, default=generate_uuid)
    aadhaar_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash of Aadhaar
    full_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    religion = Column(String(50), nullable=True)
    caste_category = Column(String(20), nullable=True)  # GENERAL, OBC, SC, ST
    sub_caste = Column(String(50), nullable=True)
    phone_primary = Column(String(20), nullable=False)
    phone_secondary = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    epic_number = Column(String(50), nullable=True)
    marital_status = Column(String(20), nullable=True)
    blood_group = Column(String(5), nullable=True)
    profile_photo_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    session_token = Column(String(255), nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    addresses = relationship("CitizenAddress", back_populates="citizen", cascade="all, delete-orphan")
    education = relationship("CitizenEducation", back_populates="citizen", cascade="all, delete-orphan")
    family_members = relationship("CitizenFamilyMember", back_populates="citizen", cascade="all, delete-orphan")
    work_experience = relationship("CitizenWorkExperience", back_populates="citizen", cascade="all, delete-orphan")
    languages = relationship("CitizenLanguage", back_populates="citizen", cascade="all, delete-orphan")
    physical_standard = relationship("CitizenPhysicalStandard", back_populates="citizen", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="citizen")
    employment_registration = relationship("EmploymentRegistration", back_populates="citizen", uselist=False)

class CitizenAddress(Base):
    __tablename__ = "citizen_addresses"

    address_id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False)
    address_type = Column(String(20), nullable=False)  # PERMANENT, PRESENT, CORRESPONDENCE
    house_no = Column(String(100), nullable=True)
    street_locality = Column(String(150), nullable=True)
    village_town = Column(String(100), nullable=False)
    post_office = Column(String(100), nullable=False)
    police_station = Column(String(100), nullable=False)
    circle = Column(String(100), nullable=True)
    sub_division = Column(String(100), nullable=True)
    district = Column(String(100), nullable=False)
    state = Column(String(100), default="Manipur")
    pin_code = Column(String(10), nullable=False)
    area_type = Column(String(10), nullable=False)  # URBAN, RURAL
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    citizen = relationship("Citizen", back_populates="addresses")

class CitizenEducation(Base):
    __tablename__ = "citizen_education"

    education_id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False)
    exam_passed = Column(String(100), nullable=False)
    board_or_university = Column(String(150), nullable=False)
    institute_name = Column(String(150), nullable=False)
    subjects_list = Column(String(255), nullable=False)
    division_or_grade = Column(String(50), nullable=False)
    percentage_or_cgpa = Column(Numeric(5, 2), nullable=False)
    year_of_passing = Column(Integer, nullable=False)
    course_duration_years = Column(Integer, nullable=False)
    instruction_medium = Column(String(50), nullable=False)
    certificate_doc_url = Column(String(255), nullable=True)
    certificate_doc_hash = Column(String(64), nullable=True)  # SHA-256
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    citizen = relationship("Citizen", back_populates="education")

class CitizenFamilyMember(Base):
    __tablename__ = "citizen_family_members"

    family_member_id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False)
    relationship_type = Column("relationship", String(20), nullable=False)  # FATHER, MOTHER, SPOUSE, GUARDIAN, SIBLING
    full_name = Column(String(100), nullable=False)
    occupation = Column(String(100), nullable=True)
    annual_income = Column(Numeric(12, 2), default=0.00)
    phone = Column(String(20), nullable=True)
    is_alive = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    citizen = relationship("Citizen", back_populates="family_members")

class CitizenWorkExperience(Base):
    __tablename__ = "citizen_work_experience"

    experience_id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False)
    employer_name = Column(String(150), nullable=False)
    post_held = Column(String(100), nullable=False)
    nature_of_work = Column(String(255), nullable=True)
    experience_type = Column(String(20), nullable=False)  # GOVERNMENT, PRIVATE, SELF_EMPLOYED
    job_type = Column(String(20), nullable=False)  # FULL_TIME, PART_TIME, CONTRACT
    pay_on_leaving = Column(Numeric(12, 2), default=0.00)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=True)
    experience_doc_url = Column(String(255), nullable=True)
    experience_doc_hash = Column(String(64), nullable=True)  # SHA-256
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    citizen = relationship("Citizen", back_populates="work_experience")

class CitizenLanguage(Base):
    __tablename__ = "citizen_languages"

    language_id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False)
    language_name = Column(String(50), nullable=False)
    can_read = Column(Boolean, default=False)
    can_write = Column(Boolean, default=False)
    can_speak = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    citizen = relationship("Citizen", back_populates="languages")

class CitizenPhysicalStandard(Base):
    __tablename__ = "citizen_physical_standards"

    physical_id = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id = Column(String(36), ForeignKey("citizens.citizen_id"), nullable=False)
    height_cm = Column(Numeric(5, 2), nullable=False)
    weight_kg = Column(Numeric(5, 2), nullable=False)
    chest_normal_cm = Column(Numeric(5, 2), nullable=False)
    chest_expanded_cm = Column(Numeric(5, 2), nullable=False)
    wears_glasses = Column(Boolean, default=False)
    disability_status = Column(String(20), default="NONE")  # NONE, PARTIAL, FULL
    disability_type = Column(String(100), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    citizen = relationship("Citizen", back_populates="physical_standard")
