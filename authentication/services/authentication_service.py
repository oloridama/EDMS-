from dataclasses import dataclass
from datetime import datetime, timedelta

from authentication.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    UsernameAlreadyExistsError,
)
from authentication.models.user import Role, User
from authentication.repositories.user_repository import (
    AuthTokenRepository,
    UserRepository,
)
from authentication.security import digest_token, generate_token, hash_password, verify_password

DEFAULT_TOKEN_TTL = timedelta(hours=12)


@dataclass(frozen=True)
class AuthToken:
    access_token: str
    expires_at: datetime


class AuthenticationService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: AuthTokenRepository,
        token_ttl: timedelta = DEFAULT_TOKEN_TTL,
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.token_ttl = token_ttl

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: Role,
    ) -> User:
        username = (username or "").strip()
        email = (email or "").strip().lower()
        if not username:
            raise ValueError("Username is required.")
        if not email or "@" not in email:
            raise ValueError("A valid email address is required.")
        if self.user_repository.get_by_username(username) is not None:
            raise UsernameAlreadyExistsError("username", username)
        if self.user_repository.get_by_email(email) is not None:
            raise UsernameAlreadyExistsError("email", email)

        return self.user_repository.create(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )

    def bootstrap_admin(
        self,
        username: str,
        email: str,
        password: str,
    ) -> User:
        """Create the first administrator, only while no users exist."""
        if self.user_repository.count() > 0:
            raise PermissionDeniedError("auth:manage")
        return self.register_user(username, email, password, Role.ADMINISTRATOR)

    def login(self, username: str, password: str) -> AuthToken:
        user = self.user_repository.get_by_username((username or "").strip())
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveUserError(user.username)

        token = generate_token()
        expires_at = self.token_repository.create(
            user.user_id,
            digest_token(token),
            self.token_ttl,
        )
        return AuthToken(access_token=token, expires_at=expires_at)

    def authenticate_token(self, token: str) -> User:
        if not token:
            raise InvalidTokenError()
        user = self.token_repository.resolve(digest_token(token))
        if user is None:
            raise InvalidTokenError()
        if not user.is_active:
            raise InactiveUserError(user.username)
        return user

    def logout(self, token: str) -> None:
        self.token_repository.revoke(digest_token(token))

    @staticmethod
    def require_permission(user: User, permission: str) -> None:
        if not user.has_permission(permission):
            raise PermissionDeniedError(permission)
