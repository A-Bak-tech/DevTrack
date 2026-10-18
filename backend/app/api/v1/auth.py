
from typing import Annotated

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core_config import settings
from app.db.dependencies import get_db
from app.models.user import User

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

from app.security.authentication import get_current_user

from app.security.csrf import (
    generate_csrf_token,
    require_csrf,
    validate_request_origin,
)

from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    login_user,
    logout_user,
    register_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# --------------------------------------------------
# USER REGISTRATION
# --------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "Email address is already registered."
        },
        403: {
            "description": "Untrusted request origin."
        },
    },
)
def register(
    registration: RegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    validate_request_origin(request)

    try:
        user = register_user(db, registration)

    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered.",
        )

    return user


# --------------------------------------------------
# USER LOGIN
# --------------------------------------------------

@router.post(
    "/login",
    responses={
        401: {
            "description": "Invalid email or password."
        },
        403: {
            "description": "Untrusted request origin."
        },
    },
)
def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    validate_request_origin(request)

    try:
        token = login_user(
            db,
            str(credentials.email),
            credentials.password,
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    response.set_cookie(
        key="devtrack_session",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    return {
        "message": "Login successful"
    }


# --------------------------------------------------
# GET CURRENT USER
# --------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return current_user


# --------------------------------------------------
# GET CSRF TOKEN
# --------------------------------------------------

@router.get("/csrf")
def get_csrf_token(
    request: Request,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    validate_request_origin(request)

    session_token = request.cookies.get(
        "devtrack_session"
    )

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    return {
        "csrf_token": generate_csrf_token(
            session_token
        )
    }


# --------------------------------------------------
# USER LOGOUT
# --------------------------------------------------

@router.post(
    "/logout",
    dependencies=[Depends(require_csrf)],
    responses={
        403: {
            "description": "Missing or invalid CSRF token."
        },
    },
)
def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[
        str | None,
        Cookie(alias="devtrack_session"),
    ] = None,
):
    if token:
        logout_user(db, token)

    response.delete_cookie(
        key="devtrack_session",
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
        httponly=True,
    )

    return {
        "message": "Logged out successfully"
    }
