
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.security.passwords import hash_password

from datetime import datetime, timezone
from app.security.sessions import hash_session_token

from app.models.session import Session as UserSession
from app.security.passwords import verify_password
from app.security.sessions import (
    generate_session_token,
    hash_session_token,
    session_expiration,
)



class EmailAlreadyRegisteredError(Exception):
    """Raised when an email address is already registered."""
    

class InvalidCredentialsError(Exception):
    """Raised when login credentials are incorrect."""


def register_user(
    db: Session,
    registration: RegisterRequest,
) -> User:
    """Create a new DevTrack user."""

    email = str(registration.email).strip().casefold()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is not None:
        raise EmailAlreadyRegisteredError(
            "Email address is already registered."
        )

    user = User(
        email=email,
        password_hash=hash_password(registration.password),
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegisteredError(
            "Email address is already registered."
        ) from exc

    return user

    
def login_user(
    db: Session,
    email: str,
    password: str,
) -> str:
    """Authenticate a user and create a database session."""

    normalized_email = email.strip().casefold()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None or not verify_password(
        password, user.password_hash
    ):
        raise InvalidCredentialsError(
            "Invalid email or password."
        )

    token = generate_session_token()

    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=session_expiration(),
    )

    db.add(session)
    db.commit()

    return token


def logout_user(
    db: Session,
    token: str,
) -> None:
    """Revoke an existing login session."""

    token_hash = hash_session_token(token)

    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == token_hash
        )
    )

    if session is None:
        return

    if session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()

