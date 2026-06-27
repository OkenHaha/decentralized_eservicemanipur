import uuid
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.simulators.aadhaar_gateway import query_central_registry, AadhaarValidationError
from app.simulators.otp_provider import generate_cryptographic_otp, dispatch_sms_gateway
from app.models.citizen import Citizen, CitizenAddress

# A simple in-memory cache for simulating active sessions, CAPTCHAs, and OTPs
# In production, this would use Redis
MOCK_CAPTCHA_CACHE = {}
MOCK_OTP_CACHE = {}
MOCK_OTP_VERIFIED = {}  # Tracks if a mobile number's OTP is verified (allows registration)

class IdentityValidationError(Exception):
    pass

def generate_captcha() -> tuple[str, str]:
    """
    Generates a mock CAPTCHA. Returns (captcha_id, captcha_text).
    """
    captcha_id = str(uuid.uuid4())
    captcha_text = str(uuid.uuid4())[:6].upper()
    MOCK_CAPTCHA_CACHE[captcha_id] = captcha_text
    return captcha_id, captcha_text

def verify_captcha(captcha_id: str, entered_value: str) -> bool:
    """
    Implements Phase 1 of SecureCitizenAadhaarIngestion.
    """
    true_value = MOCK_CAPTCHA_CACHE.get(captcha_id)
    if not true_value:
        return False
    # Check case-insensitive
    is_valid = true_value.strip().lower() == str(entered_value).strip().lower()
    if is_valid:
        # Consume CAPTCHA
        MOCK_CAPTCHA_CACHE.pop(captcha_id, None)
    return is_valid

async def send_otp_handshake(mobile: str, captcha_id: str, captcha_value: str) -> bool:
    """
    Implements Phase 2 of SecureCitizenAadhaarIngestion.
    """
    if not verify_captcha(captcha_id, captcha_value):
        raise IdentityValidationError("CAPTCHA_INVALID: Computational check failed.")
        
    otp = generate_cryptographic_otp()
    MOCK_OTP_CACHE[mobile] = otp
    dispatch_sms_gateway(mobile, otp)
    return True

async def verify_otp_handshake(mobile: str, otp_code: str) -> bool:
    """
    Verifies the One-Time Password. If valid, marks the mobile as verified.
    """
    true_otp = MOCK_OTP_CACHE.get(mobile)
    if not true_otp:
        raise IdentityValidationError("AUTH_FAILED: No active OTP request found for this number.")
        
    if true_otp == otp_code:
        # Mark as verified
        MOCK_OTP_VERIFIED[mobile] = True
        MOCK_OTP_CACHE.pop(mobile, None)  # Consume OTP
        return True
    else:
        raise IdentityValidationError("AUTH_FAILED: Invalid One-Time Token string.")

def get_sha256_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

async def register_citizen_with_aadhaar(
    db: AsyncSession,
    aadhaar_number: str,
    mobile: str,
    otp_code: str
) -> Citizen:
    """
    Implements Phase 3 of SecureCitizenAadhaarIngestion.
    Verifies OTP and queries Aadhaar registry to instantiate an immutable Citizen profile.
    """
    # 1. Verify OTP has been validated for this mobile
    is_verified = MOCK_OTP_VERIFIED.get(mobile, False)
    if not is_verified:
        # Fallback to direct verification
        await verify_otp_handshake(mobile, otp_code)
        
    # Consume verification status
    MOCK_OTP_VERIFIED.pop(mobile, None)

    # 2. Query central identity registry
    try:
        registry_payload = query_central_registry(aadhaar_number, mobile)
    except AadhaarValidationError as e:
        raise IdentityValidationError(str(e))

    # 3. Check if citizen is already registered
    aadhaar_hash = get_sha256_hash(aadhaar_number)
    stmt = select(Citizen).where(Citizen.aadhaar_hash == aadhaar_hash)
    result = await db.execute(stmt)
    existing_citizen = result.scalar_one_or_none()
    
    if existing_citizen:
        raise IdentityValidationError("CITIZEN_ALREADY_REGISTERED: A citizen with this Aadhaar has already registered.")

    # 4. Instantiate Profile freezing primary identification states (Immutable fields)
    new_citizen = Citizen(
        citizen_id=f"citizen-{str(uuid.uuid4())[:8]}",
        aadhaar_hash=aadhaar_hash,
        full_name=registry_payload["Name"],          # IMMUTABLE
        father_name=registry_payload["FatherName"],    # IMMUTABLE
        date_of_birth=registry_payload["DOB"],         # IMMUTABLE
        gender=registry_payload["Gender"],             # IMMUTABLE
        phone_primary=mobile,
        caste_category="GENERAL",  # default, user can set category
        is_active=True
    )
    
    db.add(new_citizen)
    await db.flush()  # Populates new_citizen.citizen_id

    # 5. Populate default address from Aadhaar
    # Split mock address components roughly
    address_parts = registry_payload["Address"].split(", ")
    street = address_parts[0] if len(address_parts) > 0 else ""
    district = address_parts[1] if len(address_parts) > 1 else "Imphal West"
    
    default_address = CitizenAddress(
        citizen_id=new_citizen.citizen_id,
        address_type="PERMANENT",
        street_locality=street,
        village_town=district,  # Mock mapping
        post_office="Imphal SO",
        police_station="Imphal PS",
        circle="Lamphel",
        sub_division="Lamphelpat",
        district=district,
        pin_code=registry_payload["Zip"],
        area_type="URBAN",
        is_primary=True
    )
    db.add(default_address)
    
    await db.commit()
    await db.refresh(new_citizen)
    return new_citizen
