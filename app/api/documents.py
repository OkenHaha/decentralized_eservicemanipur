from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import shutil
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_citizen
from app.models.citizen import Citizen
from app.models.application import Application, ApplicationDocument, ApplicationStatusLog
from app.models.admin import ServiceCatalog
from app.services.crypto_service import compute_sha256, compute_document_fingerprint
from app.services.ledger_service import append_genesis_block
from app.config import settings

router = APIRouter(prefix="/applications", tags=["Document Uploads"])

@router.post("/{application_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: str,
    document_type: str,
    file: UploadFile = File(...),
    citizen: Citizen = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document for an application. Compute its SHA-256 hash for anti-tampering verification.
    If all required documents are uploaded, locks the application and generates the Genesis ledger block.
    """
    # 1. Fetch application and verify ownership
    stmt = select(Application).where(Application.application_id == application_id)
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    if app.citizen_id != citizen.citizen_id:
        raise HTTPException(status_code=403, detail="Permission denied to access this application.")
    if app.current_status != "SUBMITTED" and app.current_status != "DRAFT":
        raise HTTPException(status_code=400, detail="Cannot upload documents to an application that is already under review.")

    # 2. Get service requirements and file size limit
    stmt_svc = select(ServiceCatalog).where(ServiceCatalog.service_id == app.service_id)
    res_svc = await db.execute(stmt_svc)
    service = res_svc.scalar_one()
    
    required_docs = service.required_documents_schema.get("documents", [])
    if document_type not in required_docs:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid document type. Allowed types: {', '.join(required_docs)}"
        )

    # 3. Read file and validate size
    file_bytes = await file.read()
    file_size = len(file_bytes)
    max_size_bytes = service.max_file_size_kb * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400, 
            detail=f"PAYLOAD_OVERFLOW: File exceeds the server limits of {service.max_file_size_kb} KB."
        )

    # 4. Compute SHA-256 fingerprint hash
    file_hash = compute_sha256(file_bytes)

    # Check if this exact file hash is already uploaded anywhere (to prevent duplicates/tampering)
    stmt_doc = select(ApplicationDocument).where(ApplicationDocument.file_hash == file_hash)
    res_doc = await db.execute(stmt_doc)
    existing_doc = res_doc.scalar_one_or_none()
    if existing_doc:
        raise HTTPException(status_code=400, detail="This file has already been uploaded.")

    # 5. Save file locally
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{application_id}_{document_type}{file_extension}"
    file_path = settings.UPLOAD_DIR / filename
    
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 6. Delete old doc database record of same type if exists
    stmt_old_doc = select(ApplicationDocument).where(
        ApplicationDocument.application_id == application_id,
        ApplicationDocument.document_type == document_type
    )
    res_old_doc = await db.execute(stmt_old_doc)
    old_doc = res_old_doc.scalar_one_or_none()
    if old_doc:
        await db.delete(old_doc)

    # 7. Add document record
    doc_record = ApplicationDocument(
        application_id=application_id,
        document_type=document_type,
        document_label=document_type.replace("_", " "),
        original_filename=file.filename,
        storage_url=str(file_path),
        file_hash=file_hash,
        file_size_bytes=file_size,
        mime_type=file.content_type
    )
    db.add(doc_record)
    await db.flush()

    # 8. Check if all required documents are now uploaded
    # Reload documents
    stmt_all_docs = select(ApplicationDocument).where(ApplicationDocument.application_id == application_id)
    res_all_docs = await db.execute(stmt_all_docs)
    all_uploaded = res_all_docs.scalars().all()
    uploaded_types = {d.document_type for d in all_uploaded}

    missing_docs = [r for r in required_docs if r not in uploaded_types]

    if not missing_docs:
        # All required docs uploaded! Lock files and append genesis block to ledger
        # Gather all file contents
        files_map = {}
        for d in all_uploaded:
            with open(d.storage_url, "rb") as f:
                files_map[d.document_type] = f.read()

        fingerprint = compute_document_fingerprint(files_map)
        
        # Append to blockchain ledger
        await append_genesis_block(db, application_id, fingerprint)
        
        # Update status from potential DRAFT to SUBMITTED
        if app.current_status == "DRAFT":
            app.current_status = "SUBMITTED"
            app.last_status_change_at = datetime.utcnow()
            db.add(app)
            
            status_log = ApplicationStatusLog(
                application_id=application_id,
                from_status="DRAFT",
                to_status="SUBMITTED",
                changed_by=citizen.citizen_id,
                changed_by_role="CITIZEN",
                remarks="All documents uploaded. Application locked and ledger genesis recorded."
            )
            db.add(status_log)

    await db.commit()
    
    return {
        "status": "SUCCESS",
        "message": f"Document {document_type} uploaded successfully.",
        "file_hash": file_hash,
        "is_locked_and_submitted": not missing_docs,
        "missing_documents": missing_docs
    }
