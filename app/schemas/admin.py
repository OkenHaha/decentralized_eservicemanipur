from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class RemarkCreate(BaseModel):
    remark_type: str  # OBSERVATION | QUERY | OBJECTION | INTERNAL_NOTE
    remark_text: str
    is_internal: bool = True
    requires_citizen_response: bool = False

class RemarkResponse(BaseModel):
    remark_id: str
    application_id: str
    official_id: str
    remark_type: str
    remark_text: str
    is_internal: bool
    requires_citizen_response: bool
    citizen_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AssignmentResponse(BaseModel):
    assignment_id: str
    application_id: str
    assigned_to: str
    assigned_by: str
    assignment_type: str
    assignment_status: str
    assigned_at: datetime
    deadline: Optional[datetime] = None

    class Config:
        from_attributes = True
