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
    
    # Broadcast to external simulation blockchain node
    import httpx
    from app.config import settings
    async with httpx.AsyncClient() as client:
        try:
            message_data = {
                "application_id": application_id,
                "status_at_block": status,
                "aggregate_data_hash": document_fingerprint_hash,
                "signee_address": signee_address,
                "signee_role": signee_role,
                "action_description": action_desc,
                "block_timestamp": timestamp_str,
                "block_sequence": 1
            }
            tx_payload = {
                "sender": signee_address,
                "receiver": "AuditorNode",
                "amount": 0.0,
                "message": json.dumps(message_data),
                "signature": "GenesisSignature"
            }
            res = await client.post(f"{settings.BLOCKCHAIN_NODE_URL}/transactions/new", json=tx_payload)
            if res.status_code != 200:
                raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Failed to queue transaction on external node: {res.text}")
            
            res_mine = await client.post(f"{settings.BLOCKCHAIN_NODE_URL}/mine")
            if res_mine.status_code != 200:
                raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Failed to mine block on external node: {res_mine.text}")
        except Exception as e:
            if isinstance(e, LedgerError):
                raise
            raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Could not connect to external blockchain node: {str(e)}")

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
    
    # Broadcast to external simulation blockchain node
    import httpx
    from app.config import settings
    async with httpx.AsyncClient() as client:
        try:
            message_data = {
                "application_id": application_id,
                "status_at_block": status_at_block,
                "aggregate_data_hash": latest_block.aggregate_data_hash,
                "signee_address": lambu_pub_key,
                "signee_role": "REVENUE_LAMBU",
                "action_description": action_desc,
                "block_timestamp": timestamp_str,
                "block_sequence": sequence
            }
            tx_payload = {
                "sender": lambu_pub_key,
                "receiver": "AuditorNode",
                "amount": 0.0,
                "message": json.dumps(message_data),
                "signature": lambu_signature_token
            }
            res = await client.post(f"{settings.BLOCKCHAIN_NODE_URL}/transactions/new", json=tx_payload)
            if res.status_code != 200:
                raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Failed to queue transaction on external node: {res.text}")
            
            res_mine = await client.post(f"{settings.BLOCKCHAIN_NODE_URL}/mine")
            if res_mine.status_code != 200:
                raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Failed to mine block on external node: {res_mine.text}")
        except Exception as e:
            if isinstance(e, LedgerError):
                raise
            raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Could not connect to external blockchain node: {str(e)}")
    
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
    
    # Broadcast to external simulation blockchain node
    import httpx
    from app.config import settings
    async with httpx.AsyncClient() as client:
        try:
            message_data = {
                "application_id": application_id,
                "status_at_block": status_at_block,
                "aggregate_data_hash": latest_block.aggregate_data_hash,
                "signee_address": sdo_pub_key,
                "signee_role": "SDO",
                "action_description": action_desc,
                "block_timestamp": timestamp_str,
                "block_sequence": sequence
            }
            tx_payload = {
                "sender": sdo_pub_key,
                "receiver": "AuditorNode",
                "amount": 0.0,
                "message": json.dumps(message_data),
                "signature": sdo_signature_token
            }
            res = await client.post(f"{settings.BLOCKCHAIN_NODE_URL}/transactions/new", json=tx_payload)
            if res.status_code != 200:
                raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Failed to queue transaction on external node: {res.text}")
            
            res_mine = await client.post(f"{settings.BLOCKCHAIN_NODE_URL}/mine")
            if res_mine.status_code != 200:
                raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Failed to mine block on external node: {res_mine.text}")
        except Exception as e:
            if isinstance(e, LedgerError):
                raise
            raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Could not connect to external blockchain node: {str(e)}")
    
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
    Queries the external blockchain simulation chain and filters/formats logs.
    """
    import httpx
    from app.config import settings
    from app.models.admin import GovernmentOfficial

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.BLOCKCHAIN_NODE_URL}/chain")
            if response.status_code != 200:
                raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Failed to fetch chain from node. Status: {response.status_code}")
            chain_data = response.json()
        except Exception as e:
            raise LedgerError(f"EXTERNAL_LEDGER_FAULT: Could not connect to external blockchain node: {str(e)}")

    audit_trail = []
    # Loop through blocks in the chain
    for block in chain_data.get("blocks", []):
        for tx in block.get("transactions", []):
            try:
                msg_data = json.loads(tx.get("message", "{}"))
            except json.JSONDecodeError:
                continue
            
            if msg_data.get("application_id") == application_id:
                signee_role = msg_data.get("signee_role")
                signee_address = msg_data.get("signee_address")
                
                # Fetch official designation/name if it's not a SYSTEM entry
                if signee_role != "SYSTEM":
                    stmt = select(GovernmentOfficial).where(
                        GovernmentOfficial.blockchain_wallet_address == signee_address
                    )
                    res = await db.execute(stmt)
                    official = res.scalar_one_or_none()
                    if official:
                        actor = f"{official.full_name} ({official.designation})"
                    else:
                        actor = f"Official Key: {signee_address[:10]} ({signee_role})"
                else:
                    actor = "System Gateway Node (System)"

                # Map to what PortalHome expects
                stage = msg_data.get("status_at_block")
                if stage == "SUBMITTED":
                    block_type = "GENESIS"
                elif stage == "FIELD_VERIFIED":
                    block_type = "VERIFICATION"
                elif stage == "APPROVED":
                    block_type = "APPROVAL"
                else:
                    block_type = stage

                payload_data = {}
                if block_type == "VERIFICATION":
                    verdict_val = "VERIFIED" if stage == "FIELD_VERIFIED" else "REJECTED"
                    payload_data = {
                        "verdict": verdict_val,
                        "lambu_signature_token": tx.get("signature") or ""
                    }
                elif block_type == "APPROVAL":
                    decision_val = "ISSUE" if stage == "APPROVED" else "DENY"
                    payload_data = {
                        "decision": decision_val,
                        "sdo_signature_token": tx.get("signature") or ""
                    }

                log_entry = {
                    "block_id": f"block-{block.get('index')}",
                    "block_index": block.get("index"),
                    "block_type": block_type,
                    "stage": stage,
                    "actor": actor,
                    "timestamp": msg_data.get("block_timestamp") or block.get("timestamp"),
                    "block_hash": block.get("hash") or "",
                    "prev_block_hash": block.get("previous_hash") or "",
                    "aggregate_data_hash": msg_data.get("aggregate_data_hash") or "",
                    "payload": payload_data
                }
                audit_trail.append(log_entry)
            
    return audit_trail

async def verify_ledger_integrity(db: AsyncSession, application_id: str) -> bool:
    """
    Validates the block hash integrity of the external blockchain ledger.
    """
    import httpx
    import hashlib
    from app.config import settings

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.BLOCKCHAIN_NODE_URL}/chain")
            if response.status_code != 200:
                return False
            data = response.json()
        except Exception:
            return False

    blocks = data.get("blocks", [])
    if not blocks:
        return True

    expected_prev_hash = "0"
    for idx, block in enumerate(blocks):
        # Validate sequence numbering
        if block.get("index") != idx:
            return False
            
        # Validate link hash
        if block.get("previous_hash") != expected_prev_hash:
            return False
            
        # Re-compute block hash
        txs_strings = []
        for tx in block.get("transactions", []):
            sender = tx.get("sender")
            receiver = tx.get("receiver")
            amount = tx.get("amount")
            message = tx.get("message")
            signature = tx.get("signature")
            
            if signature and signature != "None":
                if signature in ["GenesisSignature", "NetworkSignaturePlaceholder"]:
                    sig_val = signature
                else:
                    try:
                        sig_val = bytes.fromhex(signature)
                    except ValueError:
                        sig_val = signature.encode('utf-8')
            else:
                sig_val = None
                
            tx_str = f"From: {sender}, To: {receiver}, Amount: {float(amount)}, Message: {message}, Signature: {sig_val}"
            txs_strings.append(tx_str)
            
        block_string = f"{block.get('index')}{block.get('timestamp')}{txs_strings}{block.get('previous_hash')}{block.get('nonce')}".encode()
        computed_hash = hashlib.sha256(block_string).hexdigest()
        
        if block.get("hash") != computed_hash:
            return False
            
        expected_prev_hash = block.get("hash")
        
    return True
