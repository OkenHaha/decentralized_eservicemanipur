from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional

class AddressCreate(BaseModel):
    address_type: str = Field(..., description="PERMANENT | PRESENT | CORRESPONDENCE")
    house_no: Optional[str] = None
    street_locality: Optional[str] = None
    village_town: str
    post_office: str
    police_station: str
    circle: Optional[str] = None
    sub_division: Optional[str] = None
    district: str
    state: str = "Manipur"
    pin_code: str = Field(..., pattern=r"^\d{6}$")
    area_type: str = Field(..., description="URBAN | RURAL")
    is_primary: bool = False

class AddressResponse(AddressCreate):
    address_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class EducationCreate(BaseModel):
    exam_passed: str
    board_or_university: str
    institute_name: str
    subjects_list: str
    division_or_grade: str
    percentage_or_cgpa: float
    year_of_passing: int
    course_duration_years: int
    instruction_medium: str
    certificate_doc_url: Optional[str] = None
    certificate_doc_hash: Optional[str] = None
    sort_order: int = 0

class EducationResponse(EducationCreate):
    education_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class FamilyMemberCreate(BaseModel):
    relationship: str = Field(..., description="FATHER | MOTHER | SPOUSE | GUARDIAN | SIBLING")
    full_name: str
    occupation: Optional[str] = None
    annual_income: float = 0.00
    phone: Optional[str] = None
    is_alive: bool = True

class FamilyMemberResponse(FamilyMemberCreate):
    family_member_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class WorkExperienceCreate(BaseModel):
    employer_name: str
    post_held: str
    nature_of_work: Optional[str] = None
    experience_type: str = Field(..., description="GOVERNMENT | PRIVATE | SELF_EMPLOYED")
    job_type: str = Field(..., description="FULL_TIME | PART_TIME | CONTRACT")
    pay_on_leaving: float = 0.00
    from_date: date
    to_date: Optional[date] = None
    experience_doc_url: Optional[str] = None
    experience_doc_hash: Optional[str] = None

class WorkExperienceResponse(WorkExperienceCreate):
    experience_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class LanguageCreate(BaseModel):
    language_name: str
    can_read: bool = False
    can_write: bool = False
    can_speak: bool = False

class LanguageResponse(LanguageCreate):
    language_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class PhysicalStandardCreate(BaseModel):
    height_cm: float
    weight_kg: float
    chest_normal_cm: float
    chest_expanded_cm: float
    wears_glasses: bool = False
    disability_status: str = "NONE"
    disability_type: Optional[str] = None

class PhysicalStandardResponse(PhysicalStandardCreate):
    physical_id: str
    recorded_at: datetime

    class Config:
        from_attributes = True

class CitizenProfileResponse(BaseModel):
    citizen_id: str
    full_name: str
    father_name: str
    date_of_birth: date
    gender: str
    religion: Optional[str] = None
    caste_category: Optional[str] = None
    sub_caste: Optional[str] = None
    phone_primary: str
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    epic_number: Optional[str] = None
    marital_status: Optional[str] = None
    blood_group: Optional[str] = None
    profile_photo_url: Optional[str] = None
    registered_at: datetime
    
    addresses: List[AddressResponse] = []
    education: List[EducationResponse] = []
    family_members: List[FamilyMemberResponse] = []
    work_experience: List[WorkExperienceResponse] = []
    languages: List[LanguageResponse] = []
    physical_standard: Optional[PhysicalStandardResponse] = None

    class Config:
        from_attributes = True
