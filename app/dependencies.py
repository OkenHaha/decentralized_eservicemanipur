from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.config import settings
from app.models.citizen import Citizen
from app.models.admin import GovernmentOfficial

# Reuse OAuth2PasswordBearer endpoints
# We will have citizen and official OAuth2 schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise credentials_exception

async def get_current_citizen(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db)
) -> Citizen:
    if payload["role"] != "CITIZEN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation restricted to citizens."
        )
        
    stmt = select(Citizen).where(Citizen.citizen_id == payload["user_id"])
    result = await db.execute(stmt)
    citizen = result.scalar_one_or_none()
    
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Citizen account not found."
        )
    return citizen

async def get_current_official(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db)
) -> GovernmentOfficial:
    if payload["role"] == "CITIZEN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation restricted to government officials."
        )
        
    stmt = select(GovernmentOfficial).where(GovernmentOfficial.official_id == payload["user_id"])
    result = await db.execute(stmt)
    official = result.scalar_one_or_none()
    
    if not official:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Official account not found."
        )
    return official
