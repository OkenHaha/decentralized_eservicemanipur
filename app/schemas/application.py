from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional

class ServiceCatalogResponse(BaseModel):
    service_id: str
    service_code: str
    service_name: str
    department: str
    description: Optional[str] = None
    required_fields_schema: Dict[str, Any]
    required_documents_schema: Dict[str, Any]
    max_file_size_kb: int
    fee_amount: float
    expected_processing_days: int

    class Config:
        from_attributes = True

class ApplicationCreate(BaseModel):
    service_code: str
    form_data: Dict[str, Any]
    purpose: Optional[str] = None
    declaration_accepted: bool

class ApplicationDocumentResponse(BaseModel):
    document_id: str
    document_type: str
    document_label: str
    original_filename: str
    storage_url: str
    file_hash: str
    file_size_bytes: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ApplicationResponse(BaseModel):
    application_id: str
    citizen_id: str
    service_id: str
    processing_office_id: str
    current_status: str
    form_data: Dict[str, Any]
    purpose: Optional[str] = None
    declaration_accepted: bool
    rejection_reason: Optional[str] = None
    return_reason: Optional[str] = None
    priority_level: int
    submitted_at: datetime
    last_status_change_at: datetime
    expected_completion_date: Optional[datetime] = None
    created_at: datetime
    
    documents: List[ApplicationDocumentResponse] = []

    class Config:
        from_attributes = True

class ApplicationStatusLogResponse(BaseModel):
    log_id: str
    application_id: str
    from_status: Optional[str] = None
    to_status: str
    changed_by: str
    changed_by_role: str
    remarks: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True
