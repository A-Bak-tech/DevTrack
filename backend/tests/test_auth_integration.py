
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app.core_config import settings
from app.db.dependencies import get_db
from app.main import app
from app.models.user import User


from datetime import datetime, timedelta, timezone

from app.models.session import Session as UserSession
from app.security.sessions import hash_session_token
from app.security.rate_limit import limiter


# --------------------------------------------------
# TEST DATABASE CONFIGURATION
# --------------------------------------------------

TEST_DATABASE_NAME = "devtrack_test_db"

if settings.database_name == TEST_DATABASE_NAME:
    raise RuntimeError(
        "Run tests with the normal development configuration. "
        "Integration tests manage their own test database."
    )


test_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.database_user,
    password=settings.database_password,
    host=settings.database_host,
    port=settings.database_port,
    database=TEST_DATABASE_NAME,
)

test_engine = create_engine(
    test_url,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


# --------------------------------------------------
# DATABASE SAFETY CHECK
# --------------------------------------------------

def verify_test_database(db):
    """Prevent cleanup outside the dedicated test database."""

    actual_database = db.execute(
        text("SELECT current_database()")
    ).scalar_one()

    if actual_database != TEST_DATABASE_NAME:
        raise RuntimeError(
            "Refusing to modify or clean up a non-test database."
        )


# --------------------------------------------------
# TEST CLIENT AND AUTOMATIC CLEANUP
# --------------------------------------------------

@pytest.fixture
def client():
    """Create a test client and clean up users created by the test."""

    def override_get_db():
        with TestSessionLocal() as db:
            verify_test_database(db)
            yield db

    # Ensure the connection points to our test database.
    with TestSessionLocal() as db:
        verify_test_database(db)

        existing_ids = set(
            db.scalars(select(User.id)).all()
        )

        # Reset rate-limit counters before each integration test.
    limiter.limiter.storage.reset()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.pop(get_db, None)

        # Remove users created during this test.
        with TestSessionLocal() as db:
            verify_test_database(db)

            new_users = db.scalars(
                select(User).where(
                    User.id.not_in(existing_ids)
                )
            ).all()

            for user in new_users:
                db.delete(user)

            db.commit()


# --------------------------------------------------
# TEST DATA HELPER
# --------------------------------------------------

def unique_email() -> str:
    """Generate a unique email for each test."""
    return f"test-{uuid.uuid4().hex}@example.com"


# --------------------------------------------------
# TEST 1: REGISTRATION AND DUPLICATE EMAIL
# --------------------------------------------------

def test_register_and_duplicate_email(client):
    email = unique_email()

    first = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecureTestPassword123!",
        },
    )

    assert first.status_code == 201
    assert first.json()["email"] == email
    assert "password_hash" not in first.json()

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecureTestPassword123!",
        },
    )

    assert duplicate.status_code == 409


# --------------------------------------------------
# TEST 2: LOGIN AND PROTECTED ROUTE
# --------------------------------------------------

def test_login_and_protected_route(client):
    email = unique_email()
    password = "SecureTestPassword123!"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert registration.status_code == 201

    before_login = client.get("/api/v1/auth/me")
    assert before_login.status_code == 401

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login.status_code == 200
    assert "devtrack_session" in client.cookies

    me = client.get("/api/v1/auth/me")

    assert me.status_code == 200
    assert me.json()["email"] == email


# --------------------------------------------------
# TEST 3: INCORRECT PASSWORD
# --------------------------------------------------

def test_wrong_password_rejected(client):
    email = unique_email()

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecureTestPassword123!",
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "IncorrectPassword123!",
        },
    )

    assert login.status_code == 401
    assert "devtrack_session" not in login.cookies


# --------------------------------------------------
# TEST 4: CSRF-PROTECTED LOGOUT
# --------------------------------------------------

def test_csrf_logout(client):
    email = unique_email()
    password = "SecureTestPassword123!"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login.status_code == 200

    csrf = client.get("/api/v1/auth/csrf")
    assert csrf.status_code == 200

    token = csrf.json()["csrf_token"]

    # Missing CSRF token must be rejected.
    missing = client.post("/api/v1/auth/logout")
    assert missing.status_code == 403

    # Rejected logout must not invalidate the session.
    assert client.get("/api/v1/auth/me").status_code == 200

    # Valid CSRF token allows logout.
    logout = client.post(
        "/api/v1/auth/logout",
        headers={
            "X-CSRF-Token": token,
        },
    )

    assert logout.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


# --------------------------------------------------
# TEST 5: UNTRUSTED ORIGIN
# --------------------------------------------------

def test_untrusted_origin_rejected(client):
    response = client.post(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://untrusted.example",
        },
        json={
            "email": unique_email(),
            "password": "SecureTestPassword123!",
        },
    )

    assert response.status_code == 403
    assert "devtrack_session" not in response.cookies
    
    
def test_expired_session_rejected(client):
    email = unique_email()
    password = "SecureTestPassword123!"

    registration = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    token = client.cookies.get("devtrack_session")
    assert token is not None

    with TestSessionLocal() as db:
        verify_test_database(db)

        session = db.scalar(
            select(UserSession).where(
                UserSession.token_hash == hash_session_token(token)
            )
        )
        assert session is not None

        session.expires_at = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        )
        db.commit()

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_revoked_session_cannot_be_reused(client):
    email = unique_email()
    password = "SecureTestPassword123!"

    registration = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    old_token = client.cookies.get("devtrack_session")
    assert old_token is not None

    csrf = client.get("/api/v1/auth/csrf")
    assert csrf.status_code == 200

    logout = client.post(
        "/api/v1/auth/logout",
        headers={
            "X-CSRF-Token": csrf.json()["csrf_token"]
        },
    )
    assert logout.status_code == 200

    # Restore the previously revoked cookie on the test client.
    client.cookies.set(
        "devtrack_session",
        old_token,
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


    assert response.status_code == 401

def test_login_rate_limit(client):
    email = unique_email()

    for attempt in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "IncorrectPassword123!",
            },
        )

        assert response.status_code == 401, (
            f"Attempt {attempt + 1} returned "
            f"{response.status_code} instead of 401"
        )

    # The sixth login request must be rate-limited.
    blocked = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "IncorrectPassword123!",
        },
    )

    assert blocked.status_code == 429
    
    
def test_cross_site_request_rejected(client):
    response = client.post(
        "/api/v1/auth/login",
        headers={
            "Sec-Fetch-Site": "cross-site",
        },
        json={
            "email": unique_email(),
            "password": "SecureTestPassword123!",
        },
    )

    assert response.status_code == 403
    assert "devtrack_session" not in response.cookies
