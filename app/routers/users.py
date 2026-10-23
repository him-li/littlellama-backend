import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import PetUser, User
from app.schemas import UserOut, UserRoleUpdate, UserUpdate
from app.security import hash_password
from app.services import record_activity, user_payload

router = APIRouter(prefix="/user", tags=["users"])


@router.get("")
def get_users(_: AdminUser, db: DbSession) -> list[dict]:
    users = db.scalars(
        select(User).options(
            selectinload(User.pets),
            selectinload(User.saved_pet_links).selectinload(PetUser.pet),
        )
    ).all()
    return [user_payload(user, full=True) for user in users]


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, db: DbSession) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user_payload(user)


@router.get("/{user_id}/full")
def get_user_full(user_id: uuid.UUID, current: CurrentUser, db: DbSession) -> dict:
    if current.id != user_id and not current.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is not allowed")
    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.pets),
            selectinload(User.saved_pet_links).selectinload(PetUser.pet),
        )
    )
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user_payload(user, full=True)


@router.put("/{user_id}/role")
def update_user_role(
    user_id: uuid.UUID, payload: UserRoleUpdate, current: AdminUser, db: DbSession
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == current.id and payload.role != "admin":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "You cannot remove your own administrator access"
        )
    previous = "admin" if user.admin else user.role
    user.role = payload.role
    user.admin = payload.role == "admin"
    record_activity(
        db,
        "user.role_changed",
        "user",
        user.id,
        f"{user.firstname} {user.lastname}: {previous} → {payload.role}",
        actor=current,
    )
    db.commit()
    return user_payload(user, full=True)


@router.put("/{user_id}")
def update_user(
    user_id: uuid.UUID, payload: UserUpdate, current: CurrentUser, db: DbSession
) -> dict[str, str]:
    if current.id != user_id and not current.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is not allowed")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates:
        updates["email"] = str(updates["email"]).lower()
        existing = db.scalar(select(User).where(User.email == updates["email"], User.id != user.id))
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")
    if password := updates.pop("password", None):
        updates["password"] = hash_password(password)
    for key, value in updates.items():
        setattr(user, key, value)
    db.commit()
    return {"message": "User updated successfully"}
