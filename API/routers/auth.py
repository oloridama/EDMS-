from fastapi import APIRouter, Depends

from API.dependencies import get_auth_service, get_bearer_token, get_current_user
from API.schemas import (
    BootstrapRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from authentication.models.user import Role, User
from authentication.services.authentication_service import AuthenticationService

router = APIRouter(prefix="/auth", tags=["authentication"])


def user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        permissions=sorted(user.permissions),
    )


@router.post("/bootstrap", response_model=UserResponse, status_code=201)
def bootstrap_admin(
    payload: BootstrapRequest,
    service: AuthenticationService = Depends(get_auth_service),
):
    """Create the first administrator; only permitted while no users exist."""
    user = service.bootstrap_admin(payload.username, payload.email, payload.password)
    return user_response(user)


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(
    payload: RegisterRequest,
    service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    """Create a user; requires the auth:manage permission."""
    service.require_permission(current_user, "auth:manage")
    user = service.register_user(
        payload.username,
        payload.email,
        payload.password,
        Role(payload.role),
    )
    return user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    service: AuthenticationService = Depends(get_auth_service),
):
    token = service.login(payload.username, payload.password)
    return TokenResponse(
        access_token=token.access_token,
        token_type="bearer",
        expires_at=token.expires_at,
    )


@router.post("/logout", status_code=204)
def logout(
    token: str = Depends(get_bearer_token),
    service: AuthenticationService = Depends(get_auth_service),
):
    service.logout(token)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user_response(user)
