import hashlib
from typing import Dict, List, BinaryIO

def compute_sha256(data: bytes) -> str:
    """
    Computes standard SHA-256 hash for a given byte string.
    """
    return hashlib.sha256(data).hexdigest()

def combine_binary_streams(files_map: Dict[str, bytes]) -> bytes:
    """
    Implements CombineBinaryStreams from file_locking.md.
    Concatenates files sorted by their keys (types) to ensure determinism.
    """
    concatenated = bytearray()
    # Sort key-value pairs to preserve ordering
    for file_type in sorted(files_map.keys()):
        file_bytes = files_map[file_type]
        concatenated.extend(file_bytes)
    return bytes(concatenated)

def compute_document_fingerprint(files_map: Dict[str, bytes]) -> str:
    """
    Combines the uploaded documents and returns a unified SHA-256 fingerprint hash.
    Implements Step 1 of IngestAndCryptographicallyLockApplication.
    """
    concatenated = combine_binary_streams(files_map)
    return compute_sha256(concatenated)

def compute_block_hash(
    application_id: str,
    previous_block_hash: str,
    aggregate_data_hash: str,
    status_at_block: str,
    signee_address: str,
    signee_role: str,
    action_description: str,
    block_timestamp_str: str,
    block_sequence: int
) -> str:
    """
    Computes a cryptographic block hash by hashing all block fields concatenated together.
    Ensures link integrity across the append-only ledger list.
    """
    # Create deterministic text block payload
    payload = (
        f"{application_id}|"
        f"{previous_block_hash or 'GENESIS'}|"
        f"{aggregate_data_hash}|"
        f"{status_at_block}|"
        f"{signee_address}|"
        f"{signee_role}|"
        f"{action_description or ''}|"
        f"{block_timestamp_str}|"
        f"{block_sequence}"
    )
    return compute_sha256(payload.encode("utf-8"))
