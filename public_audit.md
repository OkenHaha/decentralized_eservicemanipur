ALGORITHM PublicTransparencyAudit
    INPUT: UniqueApplicationID
    OUTPUT: ChronologicalAuditTrail List

    Create AuditTrailHistory: Empty List
    CurrentTargetBlock ← QueryLatestLedgerEntry(UniqueApplicationID)

    // Back-traverse the cryptographic linked list blocks until reaching the initial submission
    WHILE CurrentTargetBlock IS NOT NULL DO
        
        // Lookup the human administrative identity mapped to the blockchain public key address
        OfficialIdentity ← LookupIdentityByAddress(CurrentTargetBlock.SigneeAddress)
        
        Create AuditCheckpointLog:
            Log.Stage     ← CurrentTargetBlock.CurrentState
            Log.Actor     ← OfficialIdentity.FullName + " (" + OfficialIdentity.Designation + ")"
            Log.Timestamp ← CurrentTargetBlock.ActionTimestamp
            Log.FileHash  ← CurrentTargetBlock.FileFingerprint

        // Prepend ensures the list reads chronologically from past to present
        Prepend AuditCheckpointLog TO AuditTrailHistory
        
        // Shift pointer back down the chain link
        CurrentTargetBlock ← GetBlockByHash(CurrentTargetBlock.PreviousStateLink)
    ENDWHILE

    RETURN AuditTrailHistory
END ALGORITHM