from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from authentication.models.user import User
from authentication.repositories.user_repository import AuthTokenRepository, UserRepository
from authentication.services.authentication_service import AuthenticationService
from shared.database import Database


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_session(database: Database = Depends(get_database)):
    with database.session_scope() as session:
        yield session


def get_auth_service(session: Session = Depends(get_session)) -> AuthenticationService:
    return AuthenticationService(
        UserRepository(session),
        AuthTokenRepository(session),
    )


def get_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    token: str = Depends(get_bearer_token),
    service: AuthenticationService = Depends(get_auth_service),
) -> User:
    try:
        return service.authenticate_token(token)
    except Exception as error:  # mapped to 401 by the app exception handlers
        raise error


def require_permission(permission: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' is required.",
            )
        return user

    return checker
