
import hashlib
import secrets
from datetime import datetime, timedelta, timezone


SESSION_DURATION = timedelta(days=7)


def generate_session_token() -> str:
    """Generate a cryptographically secure session token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Return the SHA-256 hash of a session token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiration() -> datetime:
    """Return the expiration timestamp for a new session."""
    return datetime.now(timezone.utc) + SESSION_DURATION
