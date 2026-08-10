import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserSignup(BaseModel):
    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=8, max_length=128)
    confirmPassword: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirmPassword:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str


class UserUpdate(BaseModel):
    firstname: str | None = Field(default=None, min_length=1, max_length=100)
    lastname: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=1, max_length=40)
    bio: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserOut(BaseModel):
    id: uuid.UUID
    firstname: str
    lastname: str
    email: EmailStr
    phone: str
    bio: str | None = None
    admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class PetOut(BaseModel):
    id: uuid.UUID
    type: str
    name: str
    adoption_status: str
    height: float
    weight: float
    color: str
    bio: str
    hypoallergenic: bool
    dietary_restrictions: str | None
    breed: str
    picture: str
    taken_by_user_id: uuid.UUID | None = None
    saved: bool | None = None
    relation_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class PetAction(BaseModel):
    user_id: uuid.UUID | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
