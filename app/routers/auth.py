from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import DbSession, OptionalUser
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserOut, UserSignup
from app.security import create_access_token, hash_password, verify_password
from app.services import record_activity, user_payload

router = APIRouter(tags=["authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
def signup(payload: UserSignup, db: DbSession) -> TokenResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")
    user = User(
        firstname=payload.firstName,
        lastname=payload.lastName,
        email=email,
        phone=payload.phone,
        password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    record_activity(
        db,
        "user.created",
        "user",
        user.id,
        f"New user: {user.firstname} {user.lastname}",
        actor=user,
    )
    db.commit()
    db.refresh(user)
    return TokenResponse(token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User does not exist or wrong password")
    return TokenResponse(token=create_access_token(str(user.id)))


@router.get("/login", response_model=UserOut | None)
def get_current_user(user: OptionalUser) -> dict | None:
    return user_payload(user) if user else None
