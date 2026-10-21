class UsernameAlreadyExistsError(Exception):
    """Raised when a username or email is already registered."""

    def __init__(self, field: str, value: str) -> None:
        self.field = field
        self.value = value
        super().__init__(f"A user with {field} '{value}' already exists.")


class InvalidCredentialsError(Exception):
    """Raised when a username/password combination is rejected."""

    def __init__(self) -> None:
        super().__init__("Invalid username or password.")


class InvalidTokenError(Exception):
    """Raised when a bearer token is unknown, expired, or revoked."""

    def __init__(self, reason: str = "Token is invalid or expired.") -> None:
        super().__init__(reason)


class InactiveUserError(Exception):
    """Raised when an otherwise valid user has been deactivated."""

    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"User '{username}' is inactive.")


class PermissionDeniedError(Exception):
    """Raised when an authenticated user lacks a required permission."""

    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"Permission '{permission}' is required.")
