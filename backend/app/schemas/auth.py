
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=12,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        local, domain = str(value).rsplit("@", 1)
        return f"{local.casefold()}@{domain.lower()}"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        local, domain = str(value).rsplit("@", 1)
        return f"{local.casefold()}@{domain.lower()}"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr

    model_config = {
        "from_attributes": True,
    }
