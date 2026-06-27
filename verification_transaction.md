ALGORITHM ProcessLambuFieldVerification
    INPUT: UniqueApplicationID, VerificationVerdict (VALID / INVALID), LambuDigitalSignatureToken, PresentingDocumentsMap
    OUTPUT: TransactionReceipt OR RejectionFault

    // Step 1: Read the current block state from the decentralized ledger
    ActiveRecord ← QueryLedgerByApplicationID(UniqueApplicationID)
    
    // Gatekeeper: Ensure the application isn't bypassing steps
    IF ActiveRecord.CurrentState != "SUBMITTED" THEN
        RETURN RejectionFault("PROCESS_VIOLATION: Document state transition out of sync.")
    ENDIF

    // Step 2: Anti-Cheating Check (Verify files haven't been altered since ingestion)
    CurrentFileHash ← ComputeSHA256(CombineBinaryStreams(PresentingDocumentsMap))
    IF CurrentFileHash != ActiveRecord.FileFingerprint THEN
        RETURN RejectionFault("DATA_TAMPERING: Document mismatch! Hashes do not align.")
    ENDIF

    // Step 3: Authenticate the Official's Cryptographic Identity
    LambuPublicKey ← ExtractPublicKeyFromSignature(LambuDigitalSignatureToken)
    IF VerifyRegistryAuthority(LambuPublicKey, Role: "REVENUE_LAMBU") IS NOT TRUE THEN
        RETURN RejectionFault("UNAUTHORIZED_ACCESS: Invalid hardware key token signature.")
    ENDIF

    // Step 4: Mutate state and link directly to the previous block
    Create LinkedVerificationBlock:
        Block.ApplicationID     ← UniqueApplicationID
        Block.FileFingerprint    ← ActiveRecord.FileFingerprint // Maintained integrity
        Block.CurrentState       ← (VerificationVerdict == VALID) ? "FIELD_VERIFIED" : "FIELD_REJECTED"
        Block.ActionTimestamp    ← SystemCurrentTimeUTC()
        Block.SigneeAddress      HexIdentity(LambuPublicKey)
        Block.PreviousStateLink  ← ComputeBlockHash(ActiveRecord) // Cryptographic linked list pointer

    AppendToDecentralizedLedger(LinkedVerificationBlock)
    
    RETURN TransactionReceipt(Status: "SUCCESS")
END ALGORITHM