ALGORITHM AuthorizeFinalCertificateIssuance
    INPUT: UniqueApplicationID, ApprovalDecision (ISSUE / DENY), SDODigitalSignatureToken
    OUTPUT: VerifiableCertificateObject OR AdministrativeFault

    // Step 1: Retrieve the trailing block from the ledger
    LatestBlock ← QueryLedgerByApplicationID(UniqueApplicationID)

    // Anti-Bribery Gate: SDO cannot directly approve an unverified file
    IF LatestBlock.CurrentState != "FIELD_VERIFIED" THEN
        RETURN AdministrativeFault("COMPLIANCE_BREACH: Missing mandatory field officer signature link.")
    ENDIF

    // Step 2: Verify SDO Hardware Token Authentication
    SDOPublicKey ← ExtractPublicKeyFromSignature(SDODigitalSignatureToken)
    IF VerifyRegistryAuthority(SDOPublicKey, Role: "SUB_DIVISIONAL_OFFICER") IS NOT TRUE THEN
        RETURN AdministrativeFault("SECURITY_EXCEPTION: Unverified administrative credentials.")
    ENDIF

    // Step 3: Compute Final Lifecycle Link Block
    Create FinalApprovalBlock:
        Block.ApplicationID     ← UniqueApplicationID
        Block.FileFingerprint    ← LatestBlock.FileFingerprint
        Block.CurrentState       ← (ApprovalDecision == ISSUE) ? "CERTIFICATE_ISSUED" : "APPLICATION_DENIED"
        Block.ActionTimestamp    ← SystemCurrentTimeUTC()
        Block.SigneeAddress      ← HexIdentity(SDOPublicKey)
        Block.PreviousStateLink  ← ComputeBlockHash(LatestBlock) // Linked to the Lambu's block

    AppendToDecentralizedLedger(FinalApprovalBlock)

    // Step 4: Mint the final public certificate if approved
    IF ApprovalDecision == ISSUE THEN
        CertificateQRHash ← ComputeSHA256(UniqueApplicationID + LatestBlock.FileFingerprint + SDODigitalSignatureToken)
        RETURN CreateDigitalCertificate(UniqueApplicationID, CertificateQRHash)
    ELSE
        RETURN Notification("Application Process Terminated: Rejected by Authority.")
    ENDIF
END ALGORITHM