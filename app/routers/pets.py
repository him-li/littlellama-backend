import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select

from app.dependencies import AdminUser, CurrentUser, DbSession, OptionalUser
from app.models import Pet, PetUser
from app.schemas import PetAction
from app.services import pet_payload
from app.uploads import upload_pet_image

router = APIRouter(prefix="/pet", tags=["pets"])


def get_pet_or_404(db: DbSession, pet_id: uuid.UUID) -> Pet:
    pet = db.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pet not found")
    return pet


@router.get("")
def get_pets(
    db: DbSession,
    current: OptionalUser,
    id: uuid.UUID | None = None,
    name: str = "",
    type: str = "",
    adoption_status: str = "",
    height: bool = False,
    weight: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    skip: Annotated[int, Query(ge=0)] = 0,
) -> list[dict]:
    query = select(Pet).order_by(Pet.created_at.desc()).limit(limit).offset(skip)
    filters = []
    if name:
        filters.append(Pet.name.ilike(f"%{name}%"))
    if type:
        filters.append(Pet.type.ilike(type))
    if adoption_status:
        filters.append(Pet.adoption_status.ilike(adoption_status))
    numeric_filters = []
    try:
        number = float(name)
        if height:
            numeric_filters.append(Pet.height == number)
        if weight:
            numeric_filters.append(Pet.weight == number)
    except ValueError:
        pass
    if numeric_filters:
        filters.append(or_(*numeric_filters))
    if filters:
        query = query.where(*filters)
    pets = db.scalars(query).all()
    user_id = id or (current.id if current else None)
    links = {}
    if user_id:
        links = {
            link.pet_id: link
            for link in db.scalars(select(PetUser).where(PetUser.user_id == user_id)).all()
        }
    return [pet_payload(pet, links.get(pet.id)) for pet in pets]


@router.get("/user/{user_id}")
def get_pets_by_user(user_id: uuid.UUID, current: CurrentUser, db: DbSession) -> list[dict]:
    if current.id != user_id and not current.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is not allowed")
    owned = db.scalars(select(Pet).where(Pet.taken_by_user_id == user_id)).all()
    links = db.scalars(
        select(PetUser).where(PetUser.user_id == user_id, PetUser.saved.is_(True))
    ).all()
    result = {pet.id: pet_payload(pet) for pet in owned}
    for link in links:
        result[link.pet_id] = pet_payload(link.pet, link)
    return list(result.values())


@router.get("/{pet_id}")
def get_pet(
    pet_id: uuid.UUID,
    db: DbSession,
    current: OptionalUser,
    userId: uuid.UUID | None = None,
) -> dict:
    pet = get_pet_or_404(db, pet_id)
    user_id = userId or (current.id if current else None)
    link = (
        db.scalar(select(PetUser).where(PetUser.pet_id == pet_id, PetUser.user_id == user_id))
        if user_id
        else None
    )
    return pet_payload(pet, link)


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_pet(
    _: AdminUser,
    db: DbSession,
    type: Annotated[str, Form()],
    name: Annotated[str, Form()],
    adoption_status: Annotated[str, Form()],
    height: Annotated[float, Form(gt=0)],
    weight: Annotated[float, Form(gt=0)],
    color: Annotated[str, Form()],
    bio: Annotated[str, Form()],
    hypoallergenic: Annotated[bool, Form()],
    picture: UploadFile = File(...),
    dietary_restrictions: Annotated[str, Form()] = "",
    breed: Annotated[str, Form()] = "",
) -> dict[str, str]:
    picture_url = await upload_pet_image(picture)
    pet = Pet(
        type=type,
        name=name,
        adoption_status=adoption_status,
        height=height,
        weight=weight,
        color=color,
        bio=bio,
        hypoallergenic=hypoallergenic,
        dietary_restrictions=dietary_restrictions,
        breed=breed,
        picture=picture_url,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return {"id": str(pet.id)}


@router.put("/{pet_id}")
async def edit_pet(
    pet_id: uuid.UUID,
    _: AdminUser,
    db: DbSession,
    type: Annotated[str, Form()],
    name: Annotated[str, Form()],
    adoption_status: Annotated[str, Form()],
    height: Annotated[float, Form(gt=0)],
    weight: Annotated[float, Form(gt=0)],
    color: Annotated[str, Form()],
    bio: Annotated[str, Form()],
    hypoallergenic: Annotated[bool, Form()],
    dietary_restrictions: Annotated[str, Form()] = "",
    breed: Annotated[str, Form()] = "",
    image: UploadFile | None = File(None),
) -> dict:
    pet = get_pet_or_404(db, pet_id)
    for key, value in {
        "type": type,
        "name": name,
        "adoption_status": adoption_status,
        "height": height,
        "weight": weight,
        "color": color,
        "bio": bio,
        "hypoallergenic": hypoallergenic,
        "dietary_restrictions": dietary_restrictions,
        "breed": breed,
    }.items():
        setattr(pet, key, value)
    if image:
        pet.picture = await upload_pet_image(image)
    db.commit()
    db.refresh(pet)
    return pet_payload(pet)


def require_action_user(payload: PetAction, current: CurrentUser) -> uuid.UUID:
    if payload.user_id and payload.user_id != current.id and not current.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is not allowed")
    return payload.user_id or current.id


def ensure_pet_is_available(pet: Pet) -> None:
    if pet.adoption_status != "Available" or pet.taken_by_user_id is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Pet is not available")


@router.post("/{pet_id}/adopt")
def adopt_pet(pet_id: uuid.UUID, payload: PetAction, current: CurrentUser, db: DbSession) -> dict:
    pet = get_pet_or_404(db, pet_id)
    user_id = require_action_user(payload, current)
    can_adopt = pet.adoption_status == "Available" and pet.taken_by_user_id is None
    can_adopt = can_adopt or (pet.adoption_status == "Fostered" and pet.taken_by_user_id == user_id)
    if not can_adopt:
        raise HTTPException(status.HTTP_409_CONFLICT, "Pet cannot be adopted by this user")
    pet.adoption_status = "Adopted"
    pet.taken_by_user_id = user_id
    db.commit()
    return pet_payload(pet)


@router.post("/{pet_id}/foster")
def foster_pet(pet_id: uuid.UUID, payload: PetAction, current: CurrentUser, db: DbSession) -> dict:
    pet = get_pet_or_404(db, pet_id)
    ensure_pet_is_available(pet)
    pet.adoption_status = "Fostered"
    pet.taken_by_user_id = require_action_user(payload, current)
    db.commit()
    return pet_payload(pet)


@router.post("/{pet_id}/return")
def return_pet(pet_id: uuid.UUID, current: CurrentUser, db: DbSession) -> dict:
    pet = get_pet_or_404(db, pet_id)
    if pet.taken_by_user_id != current.id and not current.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is not allowed")
    pet.adoption_status = "Available"
    pet.taken_by_user_id = None
    db.commit()
    return pet_payload(pet)


@router.post("/{pet_id}/save")
def save_pet(pet_id: uuid.UUID, payload: PetAction, current: CurrentUser, db: DbSession) -> dict:
    get_pet_or_404(db, pet_id)
    user_id = require_action_user(payload, current)
    link = db.scalar(select(PetUser).where(PetUser.pet_id == pet_id, PetUser.user_id == user_id))
    if link is None:
        link = PetUser(pet_id=pet_id, user_id=user_id, saved=True)
        db.add(link)
    else:
        link.saved = True
    db.commit()
    db.refresh(link)
    return {
        "id": str(link.id),
        "pet_id": str(link.pet_id),
        "user_id": str(link.user_id),
        "saved": True,
    }


@router.delete("/{relation_id}/save")
def unsave_pet(relation_id: uuid.UUID, current: CurrentUser, db: DbSession) -> dict[str, str]:
    link = db.get(PetUser, relation_id)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Saved pet relation not found")
    if link.user_id != current.id and not current.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is not allowed")
    db.delete(link)
    db.commit()
    return {"message": "Pet unsaved successfully"}
