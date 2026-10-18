
import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest


def test_valid_registration():
    registration = RegisterRequest(
        email="developer@example.com",
        password="SecurePassword123!",
    )

    assert registration.email == "developer@example.com"


def test_email_normalization():
    registration = RegisterRequest(
        email="Developer@Example.COM",
        password="SecurePassword123!",
    )

    assert registration.email == "developer@example.com"


def test_invalid_email_rejected():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="not-an-email",
            password="SecurePassword123!",
        )


def test_short_password_rejected():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="developer@example.com",
            password="short",
        )


def test_long_password_rejected():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="developer@example.com",
            password="a" * 129,
        )


def test_password_not_exposed_in_user_response():
    from uuid import uuid4

    from app.schemas.auth import UserResponse

    response = UserResponse(
        id=uuid4(),
        email="developer@example.com",
    )

    assert "password" not in response.model_dump()
    assert "password_hash" not in response.model_dump()
