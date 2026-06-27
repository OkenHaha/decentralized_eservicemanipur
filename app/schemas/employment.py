from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional, Dict, Any

class QualificationBlock(BaseModel):
    ExamPassed: str
    BoardOrUniversity: str
    SubjectsList: str
    DivisionOrGrade: str
    YearOfPassing: int
    CourseDurationYears: int
    InstituteName: str
    InstructionMedium: str
    PercentageOrCGPA: float

class ExperienceBlock(BaseModel):
    EmployerName: str
    PayOnLeaving: float
    FromDate: date
    ToDate: Optional[date] = None
    NatureOfWork: str
    ExperienceType: str  # GOVERNMENT | PRIVATE
    JobType: str  # FULL_TIME | PART_TIME
    PostHeld: str

class PhysicalStandardsBlock(BaseModel):
    DoWearGlasses: bool
    HeightInCm: float
    WeightInKg: float
    ChestNormalInCm: float
    BloodGroup: str

class EmploymentRegisterRequest(BaseModel):
    processing_office_code: str
    form_fields: Dict[str, Any]  # Key-value mapping of standard form fields
    QualificationsArray: List[QualificationBlock]
    LanguagesArray: List[Dict[str, Any]]
    PhysicalStandardsMap: PhysicalStandardsBlock
    CasteCategory: str = "GENERAL"
    declaration_agreement: bool

class EmploymentRenewalRequest(BaseModel):
    TargetRegistrationNumber: str
    VerifyDOB: date

class EmploymentUpdateRequest(BaseModel):
    TargetRegistrationNumber: str
    NewQualificationBlock: Optional[QualificationBlock] = None
    NewExperienceBlock: Optional[ExperienceBlock] = None
