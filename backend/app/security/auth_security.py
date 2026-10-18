
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import Session as UserSession

from app.schemas.auth import RegisterRequest

from app.security.passwords import (
    hash_password,
    verify_password,
)

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
    """Register a new DevTrack user."""

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

        # The database unique constraint also protects against
        # simultaneous registrations using the same email.
        # Only convert a known email-uniqueness violation to 409.
        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        if constraint_name == "ix_users_email":
            raise EmailAlreadyRegisteredError(
                "Email address is already registered."
            ) from exc

        raise

    return user


def login_user(
    db: Session,
    email: str,
    password: str,
) -> str:
    """Verify credentials and create a new database session."""

    normalized_email = email.strip().casefold()

    user = db.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )

    if user is None or not verify_password(
        password,
        user.password_hash,
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

    try:
        db.add(session)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise

    return token
