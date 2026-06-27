from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import bcrypt

from app.database import get_db
from app.schemas.auth import CaptchaResponse, OTPRequest, OTPVerify, RegisterRequest, Token, OfficialLoginRequest
from app.services.identity_service import generate_captcha, send_otp_handshake, verify_otp_handshake, register_citizen_with_aadhaar, IdentityValidationError
from app.dependencies import create_access_token
from app.models.citizen import Citizen
from app.models.admin import GovernmentOfficial, Role

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/captcha", response_model=CaptchaResponse)
def get_captcha():
    """
    Generate a CAPTCHA challenge for secure operations.
    """
    captcha_id, captcha_text = generate_captcha()
    return {"captcha_id": captcha_id, "captcha_text": captcha_text}

@router.post("/otp/send", status_code=status.HTTP_200_OK)
async def send_otp(request: OTPRequest):
    """
    Implements Phase 2: Send OTP to Citizen's mobile phone after validating CAPTCHA.
    """
    try:
        await send_otp_handshake(
            mobile=request.mobile,
            captcha_id=request.captcha_id,
            captcha_value=request.captcha_value
        )
        return {"status": "SUCCESS", "message": "OTP dispatched successfully."}
    except IdentityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/otp/verify", status_code=status.HTTP_200_OK)
async def verify_otp(request: OTPVerify):
    """
    Verify the OTP code sent to the citizen's mobile.
    """
    try:
        await verify_otp_handshake(mobile=request.mobile, otp_code=request.otp_code)
        return {"status": "SUCCESS", "message": "OTP verified successfully."}
    except IdentityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_citizen(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Implements Phase 3: Register a new citizen using Aadhaar ingestion.
    Locks immutable attributes retrieved from mock Aadhaar gateway registry.
    """
    try:
        new_citizen = await register_citizen_with_aadhaar(
            db=db,
            aadhaar_number=request.aadhaar_number,
            mobile=request.mobile,
            otp_code=request.otp_code
        )
        
        # Issue JWT Token upon successful registration
        token_data = {"sub": new_citizen.citizen_id, "role": "CITIZEN"}
        access_token = create_access_token(data=token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": "CITIZEN",
            "user_id": new_citizen.citizen_id,
            "name": new_citizen.full_name
        }
    except IdentityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=Token)
async def login(
    request: OfficialLoginRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint for Government Officials (SDO, Lambu, etc.).
    Also handles citizen login if the username/employee_id is a registered phone number.
    """
    # 1. Check if it's a citizen logging in (phone number login)
    if request.employee_id.isdigit() and len(request.employee_id) == 10:
        # Citizen login via mobile. In development/simulated, password acts as OTP
        phone = request.employee_id
        otp = request.password
        
        # Verify mock OTP
        if otp != "123456":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OTP code. Use '123456' for simulation login."
            )
            
        stmt = select(Citizen).where(Citizen.phone_primary == phone)
        result = await db.execute(stmt)
        citizen = result.scalar_one_or_none()
        
        if not citizen:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Citizen not registered. Register via /register first."
            )
            
        token_data = {"sub": citizen.citizen_id, "role": "CITIZEN"}
        access_token = create_access_token(data=token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": "CITIZEN",
            "user_id": citizen.citizen_id,
            "name": citizen.full_name
        }

    # 2. Otherwise login as government official
    stmt = select(GovernmentOfficial).where(GovernmentOfficial.employee_id == request.employee_id)
    result = await db.execute(stmt)
    official = result.scalar_one_or_none()

    if not official or not bcrypt.checkpw(request.password.encode("utf-8"), official.password_hash.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Employee ID or Password."
        )

    if not official.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Official account is deactivated."
        )

    # Load role code
    stmt_role = select(Role).where(Role.role_id == official.role_id)
    res_role = await db.execute(stmt_role)
    role = res_role.scalar_one()

    token_data = {"sub": official.official_id, "role": role.role_code}
    access_token = create_access_token(data=token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role.role_code,
        "user_id": official.official_id,
        "name": official.full_name
    }
