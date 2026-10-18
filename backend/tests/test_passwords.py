
import pytest

from app.security.passwords import (
    hash_password,
    password_needs_rehash,
    verify_password,
)


def test_hash_password_uses_argon2id():
    password_hash = hash_password("DevTrack-Test-123!")

    assert password_hash.startswith("$argon2id$")
    assert "DevTrack-Test-123!" not in password_hash


def test_correct_password():
    password = "DevTrack-Test-123!"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_incorrect_password():
    password_hash = hash_password("DevTrack-Test-123!")

    assert verify_password("wrong-password", password_hash) is False


def test_each_hash_uses_unique_salt():
    password = "DevTrack-Test-123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)


def test_invalid_hash():
    assert verify_password("test-password", "invalid-hash") is False


def test_current_hash_does_not_need_rehash():
    password_hash = hash_password("DevTrack-Test-123!")

    assert password_needs_rehash(password_hash) is False
