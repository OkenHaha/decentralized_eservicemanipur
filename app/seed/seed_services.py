from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.admin import ServiceCatalog

async def seed_services(db: AsyncSession):
    # Check if services already seeded
    result = await db.execute(select(ServiceCatalog))
    if result.scalars().first():
        print("Services already seeded.")
        return

    # Base fields & documents from algo_two
    base_fields = [
        "ApplicantName", "Gender", "MobileNumber", "District", 
        "SubDivision", "Circle", "Locality", "Pin Code", 
        "Purpose", "SelectedOfficeDropdown", "DeclarationCheckbox"
    ]
    base_docs = ["PassportSizePhoto", "VoterID_Proof", "ApplicantIdentityProof"]

    services = [
        {
            "service_code": "OBC_CERTIFICATE",
            "service_name": "Other Backward Classes (OBC) Certificate",
            "department": "REVENUE",
            "description": "Issuance of caste certificate for citizens belonging to OBC category.",
            "required_fields_schema": {
                "fields": base_fields + ["DateOfBirth", "PlaceOfBirth", "Religion", "SubCaste", "RelationshipDetails"]
            },
            "required_documents_schema": {
                "documents": base_docs + ["UpToDate_Jamabandi_Or_Patta", "Self_Declaration_Non_Creamy_Layer"]
            },
            "max_file_size_kb": 200,
            "fee_amount": 50.00,
            "expected_processing_days": 15
        },
        {
            "service_code": "SC_CERTIFICATE",
            "service_name": "Scheduled Caste (SC) Certificate",
            "department": "REVENUE",
            "description": "Issuance of caste certificate for citizens belonging to SC category.",
            "required_fields_schema": {
                "fields": base_fields + ["Salutation", "DateOfBirth", "PlaceOfBirth", "Religion", "SubCaste", "ParentsNames", "FamilyCasteHistoryFlag"]
            },
            "required_documents_schema": {
                "documents": base_docs
            },
            "max_file_size_kb": 200,
            "fee_amount": 50.00,
            "expected_processing_days": 15
        },
        {
            "service_code": "ST_CERTIFICATE",
            "service_name": "Scheduled Tribe (ST) Certificate",
            "department": "REVENUE",
            "description": "Issuance of tribe certificate for citizens belonging to ST category.",
            "required_fields_schema": {
                "fields": base_fields + ["DateOfBirth", "PlaceOfBirth", "Religion", "SpecificTribe", "FamilyTribeHistoryFlag"]
            },
            "required_documents_schema": {
                "documents": base_docs + ["Fathers_ST_Certificate", "Issuing_Office_Staff_Verification_Slip"]
            },
            "max_file_size_kb": 200,
            "fee_amount": 50.00,
            "expected_processing_days": 15
        },
        {
            "service_code": "PERMANENT_RESIDENT_CERTIFICATE",
            "service_name": "Permanent Resident Certificate (PRC)",
            "department": "REVENUE",
            "description": "Permanent resident certificate for education and employment purposes.",
            "required_fields_schema": {
                "fields": base_fields + ["EPIC_Number", "DateOfBirth", "PlaceOfBirth", "ResidingFromYear", "TotalPeriodOfStayInYears"]
            },
            "required_documents_schema": {
                "documents": base_docs + ["UpToDate_Jamabandi_Or_Patta"]
            },
            "max_file_size_kb": 200,
            "fee_amount": 100.00,
            "expected_processing_days": 21
        },
        {
            "service_code": "DOMICILE_CERTIFICATE",
            "service_name": "Domicile Certificate",
            "department": "REVENUE",
            "description": "Domicile certificate proving residency status in the state.",
            "required_fields_schema": {
                "fields": base_fields + ["EPIC_Number", "DateOfBirth", "PlaceOfBirth", "DateResidencyStarted", "TotalPeriodOfStayInYears", "ContinuousResidenceTenYearsCheck"]
            },
            "required_documents_schema": {
                "documents": base_docs + ["UpToDate_Jamabandi_Or_Patta"]
            },
            "max_file_size_kb": 200,
            "fee_amount": 100.00,
            "expected_processing_days": 21
        },
        {
            "service_code": "INCOME_CERTIFICATE",
            "service_name": "Income Certificate",
            "department": "REVENUE",
            "description": "Issuance of certificate certifying yearly family/individual income.",
            "required_fields_schema": {
                "fields": base_fields + ["SubmitterIdentityType", "OccupationType", "YearlyIncomeFromOccupation", "OtherSourcesIncomeAmount"]
            },
            "required_documents_schema": {
                "documents": base_docs
            },
            "max_file_size_kb": 200,
            "fee_amount": 30.00,
            "expected_processing_days": 10
        },
        {
            "service_code": "EMPLOYMENT_EXCHANGE_REGISTRATION",
            "service_name": "Employment Exchange Registration",
            "department": "EMPLOYMENT_EXCHANGE",
            "description": "Job seeker registration at District Employment Exchange.",
            "required_fields_schema": {
                "fields": [
                    "AadhaarLinkedName", "FirstName", "LastName", "EmailID", "Gender", 
                    "DateOfBirth", "MaritalStatus", "FatherName", "MotherName", "Religion", 
                    "AreaType", "PermanentAddress", "District", "PinCode", "PostOffice", 
                    "Police Station", "ProcessingOfficeDropdown", "DeclarationAgreement"
                ]
            },
            "required_documents_schema": {
                "documents": [
                    "PassportPhoto_PlainBackground", "AadhaarCard_FrontSide", 
                    "AadhaarCard_BackSide", "ProofOfResidence_Domicile", 
                    "DateOfBirth_Certificate", "Highest_Qualification_Certificate"
                ]
            },
            "max_file_size_kb": 100,  # 100 KB limit from algo_three
            "fee_amount": 0.00,
            "expected_processing_days": 7
        }
    ]

    for service_data in services:
        new_service = ServiceCatalog(**service_data)
        db.add(new_service)
        print(f"Seeding service: {service_data['service_code']}")
        
    await db.commit()
