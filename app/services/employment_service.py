from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import datetime
from dateutil.relativedelta import relativedelta

from app.models.citizen import Citizen, CitizenEducation, CitizenLanguage, CitizenPhysicalStandard, CitizenWorkExperience
from app.models.employment import EmploymentRegistration
from app.models.admin import Office, ServiceCatalog
from app.models.application import Application, ApplicationStatusLog
from app.schemas.employment import EmploymentRegisterRequest, EmploymentRenewalRequest, EmploymentUpdateRequest
from app.services.application_service import generate_sequence_token

class EmploymentExchangeError(Exception):
    pass

async def process_new_registration(
    db: AsyncSession,
    citizen: Citizen,
    request: EmploymentRegisterRequest,
    uploaded_files_sizes: dict[str, int]
) -> str:
    """
    Implements NEW_REGISTRATION workflow from algo_three.md.
    """
    # 1. Check file size limits (Strictly under 100 KB)
    for doc_type, size in uploaded_files_sizes.items():
        if size > 102400:
            raise EmploymentExchangeError("FILE_SIZE_REJECTION: All Employment Exchange documents must be strictly under 100 KB.")

    # 2. Check input array presence
    if not request.QualificationsArray:
        raise EmploymentExchangeError("DATA_DEFICIENCY: At least one educational qualification block must be defined.")
    if not request.LanguagesArray:
        raise EmploymentExchangeError("DATA_DEFICIENCY: Language proficiency table cannot be blank.")

    # 3. Check for mandatory fields in form_fields
    mandatory_fields = [
        "AadhaarLinkedName", "FirstName", "LastName", "EmailID", "Gender", 
        "DateOfBirth", "MaritalStatus", "FatherName", "MotherName", "Religion", 
        "AreaType", "PermanentAddress", "District", "PinCode", "PostOffice", 
        "Police Station", "ProcessingOfficeDropdown", "DeclarationAgreement"
    ]
    for field in mandatory_fields:
        if field not in request.form_fields or request.form_fields[field] in [None, ""]:
            raise EmploymentExchangeError(f"REGISTRATION_REJECTION: Missing field element: {field}")

    # 4. Check for mandatory documents in uploaded files
    mandatory_docs = [
        "PassportPhoto_PlainBackground", "AadhaarCard_FrontSide", 
        "AadhaarCard_BackSide", "ProofOfResidence_Domicile", "DateOfBirth_Certificate",
        "Highest_Qualification_Certificate"
    ]
    if request.CasteCategory != "GENERAL":
        mandatory_docs.append("Caste_Certificate")

    for doc in mandatory_docs:
        if doc not in uploaded_files_sizes:
            raise EmploymentExchangeError(f"REGISTRATION_REJECTION: Missing required file attachment: {doc}")

    # 5. Fetch Office
    stmt_office = select(Office).where(Office.office_code == request.processing_office_code)
    res_office = await db.execute(stmt_office)
    office = res_office.scalar_one_or_none()
    if not office:
        raise EmploymentExchangeError("OFFICE_NOT_FOUND: The selected employment exchange office was not found.")

    # Check if citizen already has a registration
    stmt_reg = select(EmploymentRegistration).where(EmploymentRegistration.citizen_id == citizen.citizen_id)
    res_reg = await db.execute(stmt_reg)
    existing_reg = res_reg.scalar_one_or_none()
    if existing_reg:
        raise EmploymentExchangeError("CITIZEN_ALREADY_REGISTERED: This citizen is already registered in the Employment Exchange.")

    # 6. Save educational qualifications, physical standards, languages, etc. to profile
    # Save qualifications
    for qual in request.QualificationsArray:
        edu = CitizenEducation(
            citizen_id=citizen.citizen_id,
            exam_passed=qual.ExamPassed,
            board_or_university=qual.BoardOrUniversity,
            institute_name=qual.InstituteName,
            subjects_list=qual.SubjectsList,
            division_or_grade=qual.DivisionOrGrade,
            percentage_or_cgpa=qual.PercentageOrCGPA,
            year_of_passing=qual.YearOfPassing,
            course_duration_years=qual.CourseDurationYears,
            instruction_medium=qual.InstructionMedium
        )
        db.add(edu)

    # Save languages
    for lang in request.LanguagesArray:
        lang_model = CitizenLanguage(
            citizen_id=citizen.citizen_id,
            language_name=lang.get("language_name"),
            can_read=lang.get("can_read", False),
            can_write=lang.get("can_write", False),
            can_speak=lang.get("can_speak", False)
        )
        db.add(lang_model)

    # Save physical standards
    phys = CitizenPhysicalStandard(
        citizen_id=citizen.citizen_id,
        height_cm=request.PhysicalStandardsMap.HeightInCm,
        weight_kg=request.PhysicalStandardsMap.WeightInKg,
        chest_normal_cm=request.PhysicalStandardsMap.ChestNormalInCm,
        chest_expanded_cm=request.PhysicalStandardsMap.ChestNormalInCm,  # Default
        wears_glasses=request.PhysicalStandardsMap.DoWearGlasses,
        disability_status="NONE",
        recorded_at=datetime.datetime.utcnow()
    )
    db.add(phys)

    # 7. Generate Registration sequence token
    new_reg_id = generate_sequence_token("MN-EMP-")
    
    # Seniority date is original registration date
    seniority_date = datetime.date.today()
    # 3 years and 3 months lifespan expiry date
    expiry_date = seniority_date + relativedelta(years=3, months=3)

    # Save physical standards snapshot in registration
    phys_snapshot = {
        "height_cm": request.PhysicalStandardsMap.HeightInCm,
        "weight_kg": request.PhysicalStandardsMap.WeightInKg,
        "chest_normal_cm": request.PhysicalStandardsMap.ChestNormalInCm,
        "wears_glasses": request.PhysicalStandardsMap.DoWearGlasses,
        "blood_group": request.PhysicalStandardsMap.BloodGroup
    }

    # 8. Create EmploymentRegistration
    new_reg = EmploymentRegistration(
        registration_id=new_reg_id,
        citizen_id=citizen.citizen_id,
        processing_office_id=office.office_id,
        current_state="PENDING_VERIFICATION",
        seniority_date=seniority_date,
        lifespan_expiry_date=expiry_date,
        renewal_count=0,
        physical_standards_snapshot=phys_snapshot
    )
    db.add(new_reg)

    # Fetch employment exchange registration service from catalog
    stmt_svc = select(ServiceCatalog).where(ServiceCatalog.service_code == "EMPLOYMENT_EXCHANGE_REGISTRATION")
    res_svc = await db.execute(stmt_svc)
    service = res_svc.scalar_one()

    # Create matching Application for queue tracking
    new_app = Application(
        application_id=new_reg_id,
        citizen_id=citizen.citizen_id,
        service_id=service.service_id,
        processing_office_id=office.office_id,
        current_status="SUBMITTED",
        form_data=request.form_fields,
        declaration_accepted=request.declaration_agreement,
        submitted_at=datetime.datetime.utcnow(),
        last_status_change_at=datetime.datetime.utcnow(),
        expected_completion_date=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )
    db.add(new_app)

    status_log = ApplicationStatusLog(
        application_id=new_app.application_id,
        from_status=None,
        to_status="SUBMITTED",
        changed_by=citizen.citizen_id,
        changed_by_role="CITIZEN",
        remarks="New Employment Exchange registration submitted."
    )
    db.add(status_log)

    await db.commit()
    return new_reg_id

async def process_renewal(
    db: AsyncSession,
    citizen: Citizen,
    request: EmploymentRenewalRequest
) -> str:
    """
    Implements RENEWAL workflow from algo_three.md.
    """
    # 1. Fetch active card from DB
    stmt_reg = select(EmploymentRegistration).where(
        EmploymentRegistration.registration_id == request.TargetRegistrationNumber
    )
    res_reg = await db.execute(stmt_reg)
    reg = res_reg.scalar_one_or_none()
    
    if not reg:
        raise EmploymentExchangeError("LEDGER_FAULT: Provided Employment Exchange Registration Number does not match active records.")

    # 2. Check that identity verification token dates align
    if request.VerifyDOB != citizen.date_of_birth:
        raise EmploymentExchangeError("AUTH_FAULT: Identity validation failed. Date of Birth mismatch.")

    # 3. Update lifespan boundaries while retaining legacy Seniority Date metrics
    current_expiry = reg.lifespan_expiry_date
    new_expiry = datetime.date.today() + relativedelta(years=3, months=3)
    
    reg.lifespan_expiry_date = new_expiry
    reg.last_renewal_date = datetime.date.today()
    reg.renewal_count += 1
    reg.current_state = "RENEWED_SUBMITTED"
    db.add(reg)

    # Log status change on the associated application
    stmt_app = select(Application).where(Application.application_id == reg.registration_id)
    res_app = await db.execute(stmt_app)
    app = res_app.scalar_one_or_none()
    if app:
        app.current_status = "UNDER_REVIEW"
        db.add(app)
        
        status_log = ApplicationStatusLog(
            application_id=app.application_id,
            from_status="SUBMITTED",
            to_status="UNDER_REVIEW",
            changed_by=citizen.citizen_id,
            changed_by_role="CITIZEN",
            remarks=f"Employment registration renewed. New Expiry: {new_expiry.isoformat()}"
        )
        db.add(status_log)

    await db.commit()
    return reg.registration_id

async def process_mutation_update(
    db: AsyncSession,
    citizen: Citizen,
    request: EmploymentUpdateRequest,
    uploaded_files_sizes: dict[str, int]
) -> str:
    """
    Implements UPDATING_QUALIFICATION_EXPERIENCE mutation from algo_three.md.
    """
    # Fetch registration
    stmt_reg = select(EmploymentRegistration).where(
        EmploymentRegistration.registration_id == request.TargetRegistrationNumber
    )
    res_reg = await db.execute(stmt_reg)
    reg = res_reg.scalar_one_or_none()
    
    if not reg:
        raise EmploymentExchangeError("LEDGER_FAULT: Provided Employment Exchange Registration Number does not match active records.")

    # 1. Update Qualification if provided
    if request.NewQualificationBlock:
        # Ensure the file verifying the qualification update is uploaded and under 100KB
        if "New_Qualification_Document" not in uploaded_files_sizes:
            raise EmploymentExchangeError("ATTACHMENT_ERROR: Updating education records requires uploading the matching certificate file.")
            
        if uploaded_files_sizes["New_Qualification_Document"] > 102400:
            raise EmploymentExchangeError("FILE_SIZE_REJECTION: Document must be strictly under 100 KB.")

        # Save qualification to citizen profile
        new_qual = CitizenEducation(
            citizen_id=citizen.citizen_id,
            exam_passed=request.NewQualificationBlock.ExamPassed,
            board_or_university=request.NewQualificationBlock.BoardOrUniversity,
            institute_name=request.NewQualificationBlock.InstituteName,
            subjects_list=request.NewQualificationBlock.SubjectsList,
            division_or_grade=request.NewQualificationBlock.DivisionOrGrade,
            percentage_or_cgpa=request.NewQualificationBlock.PercentageOrCGPA,
            year_of_passing=request.NewQualificationBlock.YearOfPassing,
            course_duration_years=request.NewQualificationBlock.CourseDurationYears,
            instruction_medium=request.NewQualificationBlock.InstructionMedium
        )
        db.add(new_qual)

    # 2. Update Experience if provided
    if request.NewExperienceBlock:
        # Verify required experience fields are present (Pydantic validates presence and types automatically!)
        new_exp = CitizenWorkExperience(
            citizen_id=citizen.citizen_id,
            employer_name=request.NewExperienceBlock.EmployerName,
            post_held=request.NewExperienceBlock.PostHeld,
            nature_of_work=request.NewExperienceBlock.NatureOfWork,
            experience_type=request.NewExperienceBlock.ExperienceType,
            job_type=request.NewExperienceBlock.JobType,
            pay_on_leaving=request.NewExperienceBlock.PayOnLeaving,
            from_date=request.NewExperienceBlock.FromDate,
            to_date=request.NewExperienceBlock.ToDate
        )
        db.add(new_exp)

    # 3. Transition status
    reg.current_state = "MUTATION_PENDING_REVIEW"
    db.add(reg)

    # Log status change on the associated application
    stmt_app = select(Application).where(Application.application_id == reg.registration_id)
    res_app = await db.execute(stmt_app)
    app = res_app.scalar_one_or_none()
    if app:
        app.current_status = "UNDER_REVIEW"
        db.add(app)
        
        status_log = ApplicationStatusLog(
            application_id=app.application_id,
            from_status="SUBMITTED",
            to_status="UNDER_REVIEW",
            changed_by=citizen.citizen_id,
            changed_by_role="CITIZEN",
            remarks="Education/experience mutation submitted."
        )
        db.add(status_log)

    await db.commit()
    return reg.registration_id
