from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.doctors import router as doctors_router
from app.api.routes.patient import router as patient_router

api_router = APIRouter()
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(doctors_router, prefix="/doctors", tags=["doctors"])
api_router.include_router(patient_router, prefix="/patient", tags=["patient"])
