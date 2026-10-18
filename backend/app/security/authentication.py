
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.session import Session as UserSession
from app.models.user import User
from app.security.sessions import hash_session_token


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[
        str | None,
        Cookie(alias="devtrack_session"),
    ] = None,
) -> User:
    """Return the authenticated user for a valid session."""

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
    )

    if not token:
        raise unauthorized

    token_hash = hash_session_token(token)

    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
        )
    )

    if session is None:
        raise unauthorized

    if session.revoked_at is not None:
        raise unauthorized

    if session.expires_at <= datetime.now(timezone.utc):
        raise unauthorized

    user = db.get(User, session.user_id)

    if user is None:
        raise unauthorized

    return user
