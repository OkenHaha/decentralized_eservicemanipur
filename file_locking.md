ALGORITHM IngestAndCryptographicallyLockApplication
    INPUT: ApplicantDataFields, DocumentFilesMap (Aadhaar, Jamabandi, IncomeSlip)
    OUTPUT: ImmutableTrackingID String, DocumentFingerprint Hash

    // Step 1: Generate a unique unalterable fingerprint of the uploaded documents
    ConcatenatedFileBuffer ← CombineBinaryStreams(DocumentFilesMap)
    
    // Compute a one-way SHA-256 cryptographic hash of the raw files
    DocumentFingerprintHash ← ComputeSHA256(ConcatenatedFileBuffer)

    // Step 2: Mint a new unique tracking token
    UniqueApplicationID ← GenerateUniqueUUID(Prefix: "MN-SEBA-TX-")

    // Step 3: Broadcast the Genesis state to the immutable block ledger
    Create BlockStateEntry:
        Block.ApplicationID  ← UniqueApplicationID
        Block.FileFingerprint ← DocumentFingerprintHash
        Block.CurrentState    ← "SUBMITTED"
        Block.ActionTimestamp ← SystemCurrentTimeUTC()
        Block.SigneeAddress   ← SystemGatewayNodeAddress
        Block.PreviousStateLink ← NULL // The anchor point of the chain

    AppendToDecentralizedLedger(BlockStateEntry)

    RETURN UniqueApplicationID, DocumentFingerprintHash
END ALGORITHM