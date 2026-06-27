from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import datetime
import random

from app.models.admin import ServiceCatalog, Office, WorkflowStage
from app.models.citizen import Citizen
from app.models.application import Application, ApplicationStatusLog
from app.models.ledger import BlockchainLedgerEntry

class ApplicationValidationError(Exception):
    pass

def generate_sequence_token(prefix: str) -> str:
    """
    Implements GenerateSequenceToken from algo_two and algo_three.
    Generates a unique reference ID.
    """
    year = datetime.datetime.utcnow().year
    random_digits = "".join(str(random.randint(0, 9)) for _ in range(5))
    return f"{prefix}{year}-{random_digits}"

async def validate_and_submit_revenue_application(
    db: AsyncSession,
    citizen: Citizen,
    service_code: str,
    form_payload: Dict[str, Any],
    declaration_accepted: bool,
    purpose: str = None
) -> Application:
    """
    Implements ValidateAndSubmitRevenueApplication from algo_two.
    """
    # 1. Structural session gatekeeper (handled by get_current_citizen)
    if not citizen.is_active:
        raise ApplicationValidationError("SECURITY_ERROR: Active citizen session not detected.")

    if not declaration_accepted:
        raise ApplicationValidationError("LEGAL_FAULT: You must accept the statutory declaration terms to submit.")

    # 2. Fetch service requirements from ServiceCatalog
    stmt = select(ServiceCatalog).where(ServiceCatalog.service_code == service_code)
    result = await db.execute(stmt)
    service = result.scalar_one_or_none()
    
    if not service:
        raise ApplicationValidationError(f"SERVICE_NOT_FOUND: The service {service_code} is not active or does not exist.")

    # 3. Field validation loop
    required_fields = service.required_fields_schema.get("fields", [])
    for field in required_fields:
        if field not in form_payload or form_payload[field] in [None, "", []]:
            raise ApplicationValidationError(f"INPUT_ERROR: Mandatory input field missing: {field}")

    # 4. Conditional business logic rules
    if service_code == "INCOME_CERTIFICATE":
        income = form_payload.get("YearlyIncomeFromOccupation")
        try:
            income_val = float(income)
            if income_val <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise ApplicationValidationError("DATA_FAULT: Declared yearly income must be a positive non-zero metric.")

    # 5. Fetch target office
    # Let's map target office dropdown selection or select the default Lamphel SDO office
    office_code = form_payload.get("SelectedOfficeDropdown", "SDO-IW")
    stmt_office = select(Office).where(Office.office_code == office_code)
    res_office = await db.execute(stmt_office)
    office = res_office.scalar_one_or_none()
    
    if not office:
        # Fallback to SDO-IW Lamphel
        stmt_fallback = select(Office).where(Office.office_code == "SDO-IW")
        res_fallback = await db.execute(stmt_fallback)
        office = res_fallback.scalar_one()

    # 6. Generate Tracking ID sequence token
    prefix = "MN-REV-"
    tracking_id = generate_sequence_token(prefix)

    # Calculate expected completion date based on catalog SLA
    sla_days = service.expected_processing_days
    expected_date = datetime.datetime.utcnow() + datetime.timedelta(days=sla_days)

    # 7. Create application record
    new_app = Application(
        application_id=tracking_id,
        citizen_id=citizen.citizen_id,
        service_id=service.service_id,
        processing_office_id=office.office_id,
        current_status="SUBMITTED",
        form_data=form_payload,
        purpose=purpose,
        declaration_accepted=declaration_accepted,
        submitted_at=datetime.datetime.utcnow(),
        last_status_change_at=datetime.datetime.utcnow(),
        expected_completion_date=expected_date
    )
    db.add(new_app)
    await db.flush()

    # Create initial status log entry
    status_log = ApplicationStatusLog(
        application_id=new_app.application_id,
        from_status=None,
        to_status="SUBMITTED",
        changed_by=citizen.citizen_id,
        changed_by_role="CITIZEN",
        remarks="Application submitted online by citizen."
    )
    db.add(status_log)

    await db.commit()
    await db.refresh(new_app)
    return new_app
