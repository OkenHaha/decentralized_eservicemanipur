from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
import json

from app.models.ledger import BlockchainLedgerEntry
from app.models.application import Application, ApplicationStatusLog
from app.models.admin import GovernmentOfficial
from app.services.crypto_service import compute_block_hash
from app.simulators.dsc_verifier import extract_public_key_from_signature, verify_registry_authority

class LedgerError(Exception):
    pass

async def get_latest_block(db: AsyncSession, application_id: str) -> BlockchainLedgerEntry:
    stmt = (
        select(BlockchainLedgerEntry)
        .where(BlockchainLedgerEntry.application_id == application_id)
        .order_by(desc(BlockchainLedgerEntry.block_sequence))
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def append_genesis_block(
    db: AsyncSession,
    application_id: str,
    document_fingerprint_hash: str
) -> BlockchainLedgerEntry:
    """
    Implements IngestAndCryptographicallyLockApplication from file_locking.md.
    Broadcasts the Genesis state to the immutable block ledger.
    """
    # Verify no block exists yet
    existing = await get_latest_block(db, application_id)
    if existing:
        raise LedgerError("LEDGER_FAULT: Genesis block already exists for this application.")

    timestamp_str = datetime.utcnow().isoformat()
    signee_address = "0xSYSTEM_GATEWAY_NODE"
    signee_role = "SYSTEM"
    status = "SUBMITTED"
    action_desc = "Application genesis entry created and locked with document hash."
    
    # Calculate hash of this block
    block_hash = compute_block_hash(
        application_id=application_id,
        previous_block_hash=None,
        aggregate_data_hash=document_fingerprint_hash,
        status_at_block=status,
        signee_address=signee_address,
        signee_role=signee_role,
        action_description=action_desc,
        block_timestamp_str=timestamp_str,
        block_sequence=1
    )

    new_block = BlockchainLedgerEntry(
        block_hash=block_hash,
        application_id=application_id,
        previous_block_hash=None,
        aggregate_data_hash=document_fingerprint_hash,
        status_at_block=status,
        signee_address=signee_address,
        signee_role=signee_role,
        action_description=action_desc,
        block_timestamp=datetime.fromisoformat(timestamp_str),
        block_sequence=1
    )
    
    db.add(new_block)
    await db.commit()
    await db.refresh(new_block)
    return new_block

async def append_verification_block(
    db: AsyncSession,
    application_id: str,
    verdict: str,  # VALID or INVALID
    lambu_signature_token: str,
    current_docs_hash: str
) -> BlockchainLedgerEntry:
    """
    Implements ProcessLambuFieldVerification from verification_transaction.md.
    """
    # 1. Retrieve the latest block
    latest_block = await get_latest_block(db, application_id)
    if not latest_block:
        raise LedgerError("PROCESS_VIOLATION: Application ledger record is missing.")
        
    # Gatekeeper check
    if latest_block.status_at_block != "SUBMITTED":
        raise LedgerError("PROCESS_VIOLATION: Document state transition out of sync.")

    # 2. Anti-Cheating check (tampering check)
    if current_docs_hash != latest_block.aggregate_data_hash:
        raise LedgerError("DATA_TAMPERING: Document mismatch! Hashes do not align.")

    # 3. Authenticate the Official's DSC Identity
    lambu_pub_key = extract_public_key_from_signature(lambu_signature_token)
    if not verify_registry_authority(lambu_pub_key, expected_role="REVENUE_LAMBU"):
        raise LedgerError("UNAUTHORIZED_ACCESS: Invalid hardware key token signature.")

    # 4. Mutate state and link directly to the previous block
    status_at_block = "FIELD_VERIFIED" if verdict == "VALID" else "FIELD_REJECTED"
    action_desc = f"Lambu field verification completed. Verdict: {verdict}"
    timestamp_str = datetime.utcnow().isoformat()
    sequence = latest_block.block_sequence + 1

    block_hash = compute_block_hash(
        application_id=application_id,
        previous_block_hash=latest_block.block_hash,
        aggregate_data_hash=latest_block.aggregate_data_hash,
        status_at_block=status_at_block,
        signee_address=lambu_pub_key,
        signee_role="REVENUE_LAMBU",
        action_description=action_desc,
        block_timestamp_str=timestamp_str,
        block_sequence=sequence
    )

    new_block = BlockchainLedgerEntry(
        block_hash=block_hash,
        application_id=application_id,
        previous_block_hash=latest_block.block_hash,
        aggregate_data_hash=latest_block.aggregate_data_hash,
        status_at_block=status_at_block,
        signee_address=lambu_pub_key,
        signee_role="REVENUE_LAMBU",
        action_description=action_desc,
        block_timestamp=datetime.fromisoformat(timestamp_str),
        block_sequence=sequence
    )
    
    db.add(new_block)
    
    # Update current status of application in database
    stmt_app = select(Application).where(Application.application_id == application_id)
    res_app = await db.execute(stmt_app)
    app = res_app.scalar_one()
    app.current_status = status_at_block
    app.last_status_change_at = datetime.utcnow()
    db.add(app)

    # Log status change
    stmt_official = select(GovernmentOfficial).where(GovernmentOfficial.blockchain_wallet_address == lambu_pub_key)
    res_official = await db.execute(stmt_official)
    official = res_official.scalar_one()

    status_log = ApplicationStatusLog(
        application_id=application_id,
        from_status="SUBMITTED",
        to_status=status_at_block,
        changed_by=official.official_id,
        changed_by_role="REVENUE_LAMBU",
        remarks=action_desc
    )
    db.add(status_log)

    await db.commit()
    await db.refresh(new_block)
    return new_block

async def append_approval_block(
    db: AsyncSession,
    application_id: str,
    decision: str,  # ISSUE or DENY
    sdo_signature_token: str
) -> BlockchainLedgerEntry:
    """
    Implements AuthorizeFinalCertificateIssuance from authorizatoin.md.
    """
    # 1. Retrieve the latest block
    latest_block = await get_latest_block(db, application_id)
    if not latest_block:
        raise LedgerError("PROCESS_VIOLATION: Application ledger record is missing.")
        
    # Anti-Bribery Gate: SDO cannot directly approve an unverified file
    if latest_block.status_at_block != "FIELD_VERIFIED":
        raise LedgerError("COMPLIANCE_BREACH: Missing mandatory field officer signature link.")

    # 2. Verify SDO Hardware Token Authentication
    sdo_pub_key = extract_public_key_from_signature(sdo_signature_token)
    if not verify_registry_authority(sdo_pub_key, expected_role="SDO") and not verify_registry_authority(sdo_pub_key, expected_role="SDC"):
        raise LedgerError("SECURITY_EXCEPTION: Unverified administrative credentials.")

    # 3. Compute Final Lifecycle Link Block
    status_at_block = "APPROVED" if decision == "ISSUE" else "REJECTED"
    action_desc = f"SDO Final decision: {decision}"
    timestamp_str = datetime.utcnow().isoformat()
    sequence = latest_block.block_sequence + 1

    block_hash = compute_block_hash(
        application_id=application_id,
        previous_block_hash=latest_block.block_hash,
        aggregate_data_hash=latest_block.aggregate_data_hash,
        status_at_block=status_at_block,
        signee_address=sdo_pub_key,
        signee_role="SDO",
        action_description=action_desc,
        block_timestamp_str=timestamp_str,
        block_sequence=sequence
    )

    new_block = BlockchainLedgerEntry(
        block_hash=block_hash,
        application_id=application_id,
        previous_block_hash=latest_block.block_hash,
        aggregate_data_hash=latest_block.aggregate_data_hash,
        status_at_block=status_at_block,
        signee_address=sdo_pub_key,
        signee_role="SDO",
        action_description=action_desc,
        block_timestamp=datetime.fromisoformat(timestamp_str),
        block_sequence=sequence
    )
    
    db.add(new_block)
    
    # Update current status of application in database
    stmt_app = select(Application).where(Application.application_id == application_id)
    res_app = await db.execute(stmt_app)
    app = res_app.scalar_one()
    app.current_status = status_at_block
    app.last_status_change_at = datetime.utcnow()
    db.add(app)

    # Log status change
    stmt_official = select(GovernmentOfficial).where(GovernmentOfficial.blockchain_wallet_address == sdo_pub_key)
    res_official = await db.execute(stmt_official)
    official = res_official.scalar_one()

    status_log = ApplicationStatusLog(
        application_id=application_id,
        from_status="FIELD_VERIFIED",
        to_status=status_at_block,
        changed_by=official.official_id,
        changed_by_role="SDO",
        remarks=action_desc
    )
    db.add(status_log)

    await db.commit()
    await db.refresh(new_block)
    return new_block

async def traverse_audit_trail(db: AsyncSession, application_id: str) -> list[dict]:
    """
    Implements PublicTransparencyAudit from public_audit.md.
    Back-traverses the cryptographic linked list blocks until reaching the initial submission.
    """
    audit_trail = []
    
    # Lookup the latest block
    current_block = await get_latest_block(db, application_id)
    
    # Back-traverse the cryptographic linked list blocks
    while current_block is not None:
        # Lookup official designation/name if it's not a SYSTEM entry
        if current_block.signee_role != "SYSTEM":
            stmt = select(GovernmentOfficial).where(
                GovernmentOfficial.blockchain_wallet_address == current_block.signee_address
            )
            res = await db.execute(stmt)
            official = res.scalar_one_or_none()
            if official:
                actor = f"{official.full_name} ({official.designation})"
            else:
                actor = f"Official Key: {current_block.signee_address[:10]} ({current_block.signee_role})"
        else:
            actor = "System Gateway Node (System)"

        log_entry = {
            "stage": current_block.status_at_block,
            "actor": actor,
            "timestamp": current_block.block_timestamp.isoformat(),
            "file_hash": current_block.aggregate_data_hash,
            "block_hash": current_block.block_hash,
            "previous_block_hash": current_block.previous_block_hash
        }
        
        # Prepend ensures the list reads chronologically from past to present
        audit_trail.insert(0, log_entry)
        
        # Shift pointer back down the chain link
        if current_block.previous_block_hash:
            stmt_prev = select(BlockchainLedgerEntry).where(
                BlockchainLedgerEntry.block_hash == current_block.previous_block_hash
            )
            res_prev = await db.execute(stmt_prev)
            current_block = res_prev.scalar_one_or_none()
        else:
            current_block = None
            
    return audit_trail

async def verify_ledger_integrity(db: AsyncSession, application_id: str) -> bool:
    """
    Calculates hashes of every block in the ledger chain dynamically to verify integrity.
    If a block hash or linked hash doesn't match the computed block hash, returns False.
    """
    stmt = (
        select(BlockchainLedgerEntry)
        .where(BlockchainLedgerEntry.application_id == application_id)
        .order_by(BlockchainLedgerEntry.block_sequence)
    )
    res = await db.execute(stmt)
    blocks = res.scalars().all()
    
    if not blocks:
        return True  # Empty ledger is technically intact
        
    expected_prev_hash = None
    for idx, block in enumerate(blocks):
        # Validate sequence numbering
        if block.block_sequence != idx + 1:
            return False
            
        # Validate link hash
        if block.previous_block_hash != expected_prev_hash:
            return False
            
        # Re-compute block hash
        computed_hash = compute_block_hash(
            application_id=block.application_id,
            previous_block_hash=block.previous_block_hash,
            aggregate_data_hash=block.aggregate_data_hash,
            status_at_block=block.status_at_block,
            signee_address=block.signee_address,
            signee_role=block.signee_role,
            action_description=block.action_description,
            block_timestamp_str=block.block_timestamp.isoformat(),
            block_sequence=block.block_sequence
        )
        
        if block.block_hash != computed_hash:
            return False
            
        expected_prev_hash = block.block_hash
        
    return True
