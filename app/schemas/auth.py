from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class CaptchaResponse(BaseModel):
    captcha_id: str
    captcha_text: str  # In production, this would only return the image, not the plain text!

class OTPRequest(BaseModel):
    mobile: str = Field(..., pattern=r"^\d{10}$")
    captcha_id: str
    captcha_value: str

class OTPVerify(BaseModel):
    mobile: str = Field(..., pattern=r"^\d{10}$")
    otp_code: str = Field(..., pattern=r"^\d{6}$")

class RegisterRequest(BaseModel):
    aadhaar_number: str = Field(..., pattern=r"^\d{12}$")
    mobile: str = Field(..., pattern=r"^\d{10}$")
    otp_code: str = Field(..., pattern=r"^\d{6}$")

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str  # CITIZEN or OFFICIAL role_code
    user_id: str  # citizen_id or official_id
    name: str

class OfficialLoginRequest(BaseModel):
    employee_id: str
    password: str
