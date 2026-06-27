# Mock DSC registry containing public key to official role mapping
MOCK_DSC_REGISTRY = {
    "0xLAMBU_KEY_IMPHAL_WEST": {
        "official_id": "lambu-imphal-west",
        "full_name": "Laishram Sanjit Singh",
        "designation": "REVENUE_LAMBU",
        "office_code": "SDO-IW",
        "is_active": True
    },
    "0xSDO_KEY_IMPHAL_WEST": {
        "official_id": "sdo-imphal-west",
        "full_name": "Dr. Ningombam Premjit Singh",
        "designation": "SDO",
        "office_code": "SDO-IW",
        "is_active": True
    },
    "0xSDC_KEY_LAMPHEL": {
        "official_id": "sdc-lamphel",
        "full_name": "Keisham Ramesh Singh",
        "designation": "SDC",
        "office_code": "SDO-IW",
        "is_active": True
    }
}

class DSCValidationError(Exception):
    pass

def extract_public_key_from_signature(signature_token: str) -> str:
    """
    Simulates extracting public key from digital signature token.
    For simulation, the signature token itself acts as the public key.
    """
    return signature_token

def verify_registry_authority(public_key: str, expected_role: str) -> bool:
    """
    Implements VerifyRegistryAuthority from verification_transaction and authorization.
    Checks if the public key belongs to a registered official with the expected role.
    """
    if public_key not in MOCK_DSC_REGISTRY:
        return False
        
    official_data = MOCK_DSC_REGISTRY[public_key]
    
    if not official_data["is_active"]:
        return False
        
    if official_data["designation"] != expected_role:
        return False
        
    return True
