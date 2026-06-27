from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import hashlib
import datetime
import random
import qrcode
import os
from pathlib import Path

from app.models.certificate import IssuedCertificate
from app.models.application import Application
from app.config import settings

def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def generate_certificate_number(cert_type: str) -> str:
    year = datetime.datetime.utcnow().year
    random_digits = "".join(str(random.randint(0, 9)) for _ in range(6))
    return f"MN-{cert_type}-{year}-{random_digits}"

async def mint_digital_certificate(
    db: AsyncSession,
    application_id: str,
    sdo_id: str,
    sdo_signature_token: str,
    file_fingerprint: str
) -> IssuedCertificate:
    """
    Implements Step 4 of AuthorizeFinalCertificateIssuance.
    Mints the final digital certificate with a QR code.
    """
    # 1. Fetch application details
    stmt = (
        select(Application)
        .where(Application.application_id == application_id)
        .options(
            selectinload(Application.service),
            selectinload(Application.citizen)
        )
    )
    res = await db.execute(stmt)
    app = res.scalar_one()

    # 2. Compute Certificate QR hash
    qr_payload = f"{application_id}|{file_fingerprint}|{sdo_signature_token}"
    qr_hash = compute_sha256(qr_payload)

    # 3. Generate certificate type from service catalog code
    cert_type = app.service.service_code.replace("_CERTIFICATE", "")
    cert_number = generate_certificate_number(cert_type)

    # 4. Generate QR code image
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    qr_filename = f"{cert_number}_QR.png"
    qr_path = settings.UPLOAD_DIR / qr_filename
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"http://localhost:8000/api/v1/audit/{application_id}")  # Verification URL
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_path)

    # 5. Create PDF placeholder file
    pdf_filename = f"{cert_number}.pdf"
    pdf_path = settings.UPLOAD_DIR / pdf_filename
    with open(pdf_path, "w") as f:
        f.write(f"MANIPUR STATE GOVERNMENT\nOfficial Digital Certificate: {cert_number}\n"
                f"Applicant: {app.citizen.full_name}\n"
                f"Service Type: {app.service.service_name}\n"
                f"Issued By: {sdo_id}\n"
                f"Date of Issue: {datetime.date.today()}\n"
                f"Status: VALID\n"
                f"Security Verification QR Hash: {qr_hash}\n")

    # 6. Compute certificate file hash
    with open(pdf_path, "rb") as f:
        cert_hash = compute_sha256(f.read().decode("utf-8", errors="ignore"))

    # 7. Save to DB
    issued_cert = IssuedCertificate(
        application_id=application_id,
        citizen_id=app.citizen_id,
        issued_by=sdo_id,
        certificate_number=cert_number,
        certificate_type=cert_type,
        certificate_hash=cert_hash,
        qr_code_hash=qr_hash,
        qr_code_image_url=str(qr_path),
        certificate_pdf_url=str(pdf_path),
        valid_from=datetime.date.today(),
        valid_until=None  # Permanent by default
    )
    db.add(issued_cert)
    await db.flush()

    return issued_cert
