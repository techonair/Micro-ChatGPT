from fastapi import APIRouter, Depends

from app.api.deps import get_app_settings, get_auth_service
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest
from app.schemas.common import ApiResponse, ok
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=ApiResponse[AuthResponse])
async def signup(
    payload: SignupRequest,
    service: AuthService = Depends(get_auth_service),
    settings=Depends(get_app_settings),
) -> ApiResponse[AuthResponse]:
    result = await service.signup(payload, settings)
    return ok(result)


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
    settings=Depends(get_app_settings),
) -> ApiResponse[AuthResponse]:
    result = await service.login(payload, settings)
    return ok(result)
