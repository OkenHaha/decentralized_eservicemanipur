from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.citizen import router as citizen_router
from app.api.applications import router as applications_router
from app.api.documents import router as documents_router
from app.api.verification import router as verification_router
from app.api.authorization import router as authorization_router
from app.api.audit import router as audit_router
from app.api.employment import router as employment_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(citizen_router)
api_router.include_router(applications_router)
api_router.include_router(documents_router)
api_router.include_router(verification_router)
api_router.include_router(authorization_router)
api_router.include_router(audit_router)
api_router.include_router(employment_router)
