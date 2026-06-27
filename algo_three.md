ALGORITHM ProcessEmploymentExchangeMutation
    INPUT: CitizenProfile, ActionWorkflow, MetadataPayload, DocumentManifestMap
    OUTPUT: SystemReferenceID String OR LedgerFault

    // 1. Initial Structural File Capacity Gatekeeper (100 KB Edge Limit)
    FOR EACH UploadedFile IN DocumentManifestMap DO
        IF UploadedFile.SizeInBytes > 102400 THEN
            RETURN LedgerFault("FILE_SIZE_REJECTION: All Employment Exchange documents must be strictly under 100 KB.")
        ENDIF
    ENDFOR

    // 2. Form Field and Attachment Manifest Definition Matrix
    Create MandatoryFields: List
    Create MandatoryDocs: List

    MandatoryFields ← ["AadhaarLinkedName", "FirstName", "LastName", "EmailID", "Gender", "DateOfBirth", "MaritalStatus", "FatherName", "MotherName", "Religion", "AreaType", "PermanentAddress", "District", "PinCode", "PostOffice", "Police Station", "ProcessingOfficeDropdown", "DeclarationAgreement"]
    MandatoryDocs   ← ["PassportPhoto_PlainBackground", "AadhaarCard_FrontSide", "AadhaarCard_BackSide", "ProofOfResidence_Domicile", "DateOfBirth_Certificate"]

    // 3. Evaluate Workflow Pipeline Paths
    CASE ActionWorkflow OF
        
        "NEW_REGISTRATION":
            // Enforce Input Arrays Presence
            IF MetadataPayload.QualificationsArray IS EMPTY THEN
                RETURN LedgerFault("DATA_DEFICIENCY: At least one educational qualification block must be defined.")
            ENDIF
            
            IF MetadataPayload.LanguagesArray IS EMPTY THEN
                RETURN LedgerFault("DATA_DEFICIENCY: Language proficiency table cannot be blank.")
            ENDIF

            // Structural checking of nested loop data schemas
            FOR EACH Qualification IN MetadataPayload.QualificationsArray DO
                RequiredQualFields ← ["ExamPassed", "BoardOrUniversity", "SubjectsList", "DivisionOrGrade", "YearOfPassing", "CourseDurationYears", "InstituteName", "InstructionMedium", "PercentageOrCGPA"]
                FOR EACH Field IN RequiredQualFields DO
                    IF Qualification[Field] == EMPTY OR Qualification[Field] == NULL THEN
                        RETURN LedgerFault("SUB_SCHEMA_ERROR: Education record element missing standard field: " + Field)
                    ENDIF
                ENDFOR
            ENDFOR

            // Core Physical Metric Structural Check
            PhysicalData ← MetadataPayload.PhysicalStandardsMap
            RequiredMetrics ← ["DoWearGlasses", "HeightInCm", "WeightInKg", "ChestNormalInCm", "BloodGroup"]
            FOR EACH Metric IN RequiredMetrics DO
                IF PhysicalData[Metric] == EMPTY OR PhysicalData[Metric] == NULL THEN
                    RETURN LedgerFault("METRIC_ERROR: Mandatory physical validation field missing: " + Metric)
                ENDIF
            ENDFOR

            // Complete Document Check Loops
            MandatoryDocs ← MandatoryDocs + ["Highest_Qualification_Certificate"]
            IF MetadataPayload.CasteCategory != "GENERAL" THEN
                Append "Caste_Certificate" TO MandatoryDocs
            ENDIF

            // Run Identity verification loop checks
            FOR EACH Field IN MandatoryFields DO
                IF MetadataPayload.FormFields[Field] == EMPTY THEN
                    RETURN LedgerFault("REGISTRATION_REJECTION: Missing field element: " + Field)
                ENDIF
            ENDFOR

            FOR EACH Doc IN MandatoryDocs DO
                IF Doc NOT IN DocumentManifestMap THEN
                    RETURN LedgerFault("REGISTRATION_REJECTION: Missing required file attachment: " + Doc)
                ENDIF
            ENDFOR

            // Generate New Active Card
            NewRegistryID ← GenerateSequenceToken(Prefix: "MN-EMP-")
            GlobalRegistryDB[NewRegistryID] ← CreateJobSeekerStructure(MetadataPayload, Status: "PENDING_VERIFICATION", SeniorityDate: SystemTime())
            RETURN NewRegistryID

        "RENEWAL":
            TargetCardID ← MetadataPayload.TargetRegistrationNumber
            IF TargetCardID NOT IN GlobalRegistryDB THEN
                RETURN LedgerFault("LEDGER_FAULT: Provided Employment Exchange Registration Number does not match active records.")
            ENDIF
            
            // Check that identity verification token dates align
            IF MetadataPayload.VerifyDOB != GlobalRegistryDB[TargetCardID].DOB THEN
                RETURN LedgerFault("AUTH_FAULT: Identity validation failed. Date of Birth mismatch.")
            ENDIF

            // Update lifespan boundaries while retaining legacy Seniority Date metrics
            GlobalRegistryDB[TargetCardID].LifespanExpiryDate ← ComputeDateOffset(CurrentTime(), Years: 3, GraceMonths: 3)
            GlobalRegistryDB[TargetCardID].CurrentState ← "RENEWED_SUBMITTED"
            RETURN TargetCardID

        "UPDATING_QUALIFICATION_EXPERIENCE":
            TargetCardID ← MetadataPayload.TargetRegistrationNumber
            ActiveRecord ← GlobalRegistryDB[TargetCardID]
            
            // Validate and patch dynamic append requests
            IF MetadataPayload.NewQualificationBlock != NULL THEN
                // Ensure the file verifying the qualification update is appended under 100KB
                IF "New_Qualification_Document" NOT IN DocumentManifestMap THEN
                    RETURN LedgerFault("ATTACHMENT_ERROR: Updating education records requires uploading the matching certificate file.")
                ENDIF
                Append MetadataPayload.NewQualificationBlock TO ActiveRecord.EducationLedger
            ENDIF

            IF MetadataPayload.NewExperienceBlock != NULL THEN
                RequiredExpFields ← ["EmployerName", "PayOnLeaving", "FromDate", "ToDate", "NatureOfWork", "ExperienceType", "JobType", "PostHeld"]
                FOR EACH ExpField IN RequiredExpFields DO
                    IF MetadataPayload.NewExperienceBlock[ExpField] == EMPTY THEN
                        RETURN LedgerFault("SUB_SCHEMA_ERROR: Appended experience block missing parameter: " + ExpField)
                    ENDIF
                ENDFOR
                Append MetadataPayload.NewExperienceBlock TO ActiveRecord.ExperienceLedger
            ENDIF

            ActiveRecord.CurrentState ← "MUTATION_PENDING_REVIEW"
            RETURN TargetCardID

    ENDCASE
END ALGORITHM