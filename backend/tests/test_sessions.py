
from datetime import datetime, timezone

from app.security.sessions import (
    generate_session_token,
    hash_session_token,
    session_expiration,
)


def test_session_tokens_are_unique():
    assert generate_session_token() != generate_session_token()


def test_session_token_hash_is_sha256():
    token = generate_session_token()
    token_hash = hash_session_token(token)

    assert len(token_hash) == 64
    assert token_hash != token


def test_session_token_hash_is_deterministic():
    token = generate_session_token()

    assert hash_session_token(token) == hash_session_token(token)


def test_session_has_future_expiration():
    expires = session_expiration()

    assert expires.tzinfo is not None
    assert expires > datetime.now(timezone.utc)
