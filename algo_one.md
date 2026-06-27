ALGORITHM SecureCitizenAadhaarIngestion
    INPUT: CitizenMobileNumber, UserEnteredCaptcha, TrueCaptchaValue
    OUTPUT: ValidatedCitizenProfile Object OR ExecutionFault

    // Phase 1: Gateway Security Check
    IF UserEnteredCaptcha != TrueCaptchaValue THEN
        RETURN ExecutionFault("CAPTCHA_INVALID: Computational check failed.")
    ENDIF

    // Phase 2: Outbound Telephony Handshake
    SecureOTPOptin ← GenerateCryptographicOTP(Length: 6)
    DispatchSMSGateway(Target: CitizenMobileNumber, Payload: SecureOTPOptin)
    
    EnteredVerificationToken ← AwaitUserOTPInput()

    IF EnteredVerificationToken == SecureOTPOptin THEN
        // Phase 3: Secure Handshake with Identity Registry
        CitizenAadhaarCardNumber ← RequestUserAadhaarString()
        RegistryPayload ← QueryCentralRegistry(AadhaarID: CitizenAadhaarCardNumber, Mobile: CitizenMobileNumber)
        
        // Instantiate Profile freezing primary identification states
        Create CitizenProfile:
            Profile.AadhaarNumber   ← RegistryPayload.AadhaarNumber // Masked internally
            Profile.FullName        ← RegistryPayload.Name          // IMMUTABLE
            Profile.DateOfBirth     ← RegistryPayload.DOB           // IMMUTABLE
            Profile.Gender          ← RegistryPayload.Gender        // IMMUTABLE
            Profile.FatherName      ← RegistryPayload.FatherName    // IMMUTABLE
            Profile.BaseStreet      ← RegistryPayload.Address       // IMMUTABLE
            Profile.PinCode         ← RegistryPayload.Zip           // IMMUTABLE
            Profile.Email           ← Null
            Profile.CasteCategory   ← Null
            Profile.SessionStatus   ← ACTIVE
            
        RETURN CitizenProfile
    ELSE
        RETURN ExecutionFault("AUTH_FAILED: Invalid One-Time Token string.")
    ENDIF
END ALGORITHM