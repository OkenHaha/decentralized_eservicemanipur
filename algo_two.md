ALGORITHM ValidateAndSubmitRevenueApplication
    INPUT: CitizenProfile, ServiceType, FormPayloadMap, DocumentUploadsMap
    OUTPUT: TrackingID String OR ValidationFault

    // 1. Structural Session Gatekeeper
    IF CitizenProfile.SessionStatus IS NOT ACTIVE THEN
        RETURN ValidationFault("SECURITY_ERROR: Active citizen session not detected.")
    ENDIF

    // 2. Define Explicit Mandatory Requirements Blueprints
    Create FieldRequirementsSchema: Dictionary
    Create DocumentRequirementsSchema: Dictionary

    // Establish Base Requirements common across all Revenue workflows
    BaseFields ← ["ApplicantName", "Gender", "MobileNumber", "District", "SubDivision", "Circle", "Locality", "Pin Code", "Purpose", "SelectedOfficeDropdown", "DeclarationCheckbox"]
    BaseDocs   ← ["PassportSizePhoto", "VoterID_Proof", "ApplicantIdentityProof"]

    // Map specific validations based on target service selection
    CASE ServiceType OF
        "OBC_CERTIFICATE":
            FieldRequirementsSchema ← BaseFields + ["DateOfBirth", "PlaceOfBirth", "Religion", "SubCaste", "RelationshipDetails"]
            DocumentRequirementsSchema ← BaseDocs + ["UpToDate_Jamabandi_Or_Patta", "Self_Declaration_Non_Creamy_Layer"]

        "SC_CERTIFICATE":
            FieldRequirementsSchema ← BaseFields + ["Salutation", "DateOfBirth", "PlaceOfBirth", "Religion", "SubCaste", "ParentsNames", "FamilyCasteHistoryFlag"]
            DocumentRequirementsSchema ← BaseDocs // Relies on core identity verification data

        "ST_CERTIFICATE":
            FieldRequirementsSchema ← BaseFields + ["DateOfBirth", "PlaceOfBirth", "Religion", "SpecificTribe", "FamilyTribeHistoryFlag"]
            DocumentRequirementsSchema ← BaseDocs + ["Fathers_ST_Certificate", "Issuing_Office_Staff_Verification_Slip"]

        "PERMANENT_RESIDENT_CERTIFICATE":
            FieldRequirementsSchema ← BaseFields + ["EPIC_Number", "DateOfBirth", "PlaceOfBirth", "ResidingFromYear", "TotalPeriodOfStayInYears"]
            DocumentRequirementsSchema ← BaseDocs + ["UpToDate_Jamabandi_Or_Patta"]

        "DOMICILE_CERTIFICATE":
            FieldRequirementsSchema ← BaseFields + ["EPIC_Number", "DateOfBirth", "PlaceOfBirth", "DateResidencyStarted", "TotalPeriodOfStayInYears", "ContinuousResidenceTenYearsCheck"]
            DocumentRequirementsSchema ← BaseDocs + ["UpToDate_Jamabandi_Or_Patta"]

        "INCOME_CERTIFICATE":
            FieldRequirementsSchema ← BaseFields + ["SubmitterIdentityType", "OccupationType", "YearlyIncomeFromOccupation", "OtherSourcesIncomeAmount"]
            DocumentRequirementsSchema ← BaseDocs // Optional slots like Lambu Slips handled via conditional pipelines
    ENDCASE

    // 3. Execution Phase 1: Input Field Validation Loop
    FOR EACH RequiredField IN FieldRequirementsSchema DO
        IF RequiredField NOT IN FormPayloadMap OR FormPayloadMap[RequiredField] == EMPTY OR FormPayloadMap[RequiredField] == NULL THEN
            RETURN ValidationFault("INPUT_ERROR: Mandatory input field missing: " + RequiredField)
        ENDIF
    ENDFOR

    // Conditional Business Logic Rule Evaluation
    IF ServiceType == "INCOME_CERTIFICATE" AND FormPayloadMap["YearlyIncomeFromOccupation"] <= 0 THEN
        RETURN ValidationFault("DATA_FAULT: Declared yearly income must be a positive non-zero metric.")
    ENDIF
    
    IF FormPayloadMap["DeclarationCheckbox"] IS NOT TRUE THEN
        RETURN ValidationFault("LEGAL_FAULT: You must accept the statutory declaration terms to submit.")
    ENDIF

    // 4. Execution Phase 2: Document Presence & Payload Ceiling Audit
    FOR EACH RequiredDoc IN DocumentRequirementsSchema DO
        IF RequiredDoc NOT IN DocumentUploadsMap THEN
            RETURN ValidationFault("ATTACHMENT_ERROR: Missing mandatory file: " + RequiredDoc)
        ENDIF

        FileStream ← DocumentUploadsMap[RequiredDoc]
        // Rigid 200 KB Boundary check execution
        IF FileStream.SizeInBytes > 204800 THEN
            RETURN ValidationFault("PAYLOAD_OVERFLOW: '" + RequiredDoc + "' exceeds the server limits of 200 KB.")
        ENDIF
    ENDFOR

    // 5. Commit Validated Record to Transaction Ledger
    GeneratedTrackToken ← GenerateSequenceToken(Prefix: "MN-REV-")
    CentralLedgerDB[GeneratedTrackToken] ← SecureApplicationRecord(
        Identity: CitizenProfile.FullName,
        Service: ServiceType,
        Data: FormPayloadMap,
        Office: FormPayloadMap["SelectedOfficeDropdown"],
        State: "SUBMITTED",
        Timestamp: SystemTime()
    )

    RETURN GeneratedTrackToken
END ALGORITHM