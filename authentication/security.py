import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Hash a password with a per-user salt using PBKDF2-HMAC-SHA256."""
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Constant-time verification of a password against its stored hash."""
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        int(iterations),
    )
    return hmac.compare_digest(candidate, expected)


def generate_token() -> str:
    """Generate an opaque bearer token; only its digest is stored server-side."""
    return secrets.token_urlsafe(32)


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
