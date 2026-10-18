
import hmac
import secrets

from fastapi import HTTPException, Request, status

from app.core_config import settings


CSRF_HEADER = "X-CSRF-Token"


def generate_csrf_token(session_token: str) -> str:
    """Generate a CSRF token tied to a login session."""

    nonce = secrets.token_urlsafe(32)

    signature = hmac.new(
        session_token.encode("utf-8"),
        nonce.encode("utf-8"),
        "sha256",
    ).hexdigest()

    return f"{nonce}.{signature}"


def verify_csrf_token(
    session_token: str,
    csrf_token: str,
) -> bool:
    """Verify that a CSRF token belongs to a session."""

    if not csrf_token:
        return False

    try:
        nonce, signature = csrf_token.split(".", 1)
    except ValueError:
        return False

    expected_signature = hmac.new(
        session_token.encode("utf-8"),
        nonce.encode("utf-8"),
        "sha256",
    ).hexdigest()

    return hmac.compare_digest(
        signature,
        expected_signature,
    )



def validate_request_origin(request: Request) -> None:
    """Reject untrusted Origin and cross-site browser requests."""

    origin = request.headers.get("origin")

    # Reject an explicitly untrusted Origin.
    if origin is not None:
        if origin not in settings.allowed_origins:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Untrusted request origin.",
            )

    # Fetch Metadata gives additional protection against
    # requests initiated from unrelated websites.
    fetch_site = request.headers.get("sec-fetch-site")

    if fetch_site == "cross-site":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-site requests are not allowed.",
        )



def require_csrf(request: Request) -> None:
    """Require a CSRF token for cookie-authenticated writes."""

    validate_request_origin(request)

    session_token = request.cookies.get("devtrack_session")
    csrf_token = request.headers.get(CSRF_HEADER)

    if not session_token or not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing.",
        )

    if not verify_csrf_token(session_token, csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token.",
        )
