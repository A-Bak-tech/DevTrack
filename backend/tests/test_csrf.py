
from app.security.csrf import (
    generate_csrf_token,
    verify_csrf_token,
)


def test_valid_csrf_token():
    session = "test-session"
    token = generate_csrf_token(session)

    assert verify_csrf_token(session, token)


def test_wrong_session_rejected():
    token = generate_csrf_token("session-one")

    assert not verify_csrf_token("session-two", token)


def test_invalid_token_rejected():
    assert not verify_csrf_token("session", "invalid")


def test_tampered_token_rejected():
    token = generate_csrf_token("session")
    nonce, signature = token.split(".", 1)

    tampered = f"{nonce}.{'0' * len(signature)}"

    assert not verify_csrf_token("session", tampered)


def test_tokens_are_unique():
    session = "test-session"

    assert generate_csrf_token(session) != generate_csrf_token(session)
