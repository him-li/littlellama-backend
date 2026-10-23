from typing import Any

from sqlalchemy import select

from app.models import ActivityEvent, Notification, Pet, PetUser, User


def pet_payload(pet: Pet, link: PetUser | None = None) -> dict[str, Any]:
    return {
        "id": pet.id,
        "type": pet.type,
        "name": pet.name,
        "adoption_status": pet.adoption_status,
        "height": pet.height,
        "weight": pet.weight,
        "color": pet.color,
        "bio": pet.bio,
        "hypoallergenic": pet.hypoallergenic,
        "dietary_restrictions": pet.dietary_restrictions,
        "breed": pet.breed,
        "picture": pet.picture,
        "taken_by_user_id": pet.taken_by_user_id,
        "saved": link.saved if link else False,
        "relation_id": link.id if link else None,
    }


def user_payload(user: User, full: bool = False) -> dict[str, Any]:
    data = {
        "id": user.id,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "email": user.email,
        "phone": user.phone,
        "bio": user.bio,
        "admin": user.admin,
        "role": "admin" if user.admin else user.role,
    }
    if full:
        data["owned_pets"] = [pet_payload(pet) for pet in user.pets]
        data["saved_pets"] = [pet_payload(link.pet, link) for link in user.saved_pet_links]
    return data


def record_activity(
    db, event_type: str, subject_type: str, subject_id, title: str, *, actor=None, detail=None
) -> None:
    db.add(
        ActivityEvent(
            event_type=event_type,
            actor_user_id=actor.id if actor else None,
            subject_type=subject_type,
            subject_id=str(subject_id),
            title=title,
            detail=detail,
        )
    )


def notify_new_pet(db, pet: Pet) -> None:
    for user_id in db.scalars(select(User.id)).all():
        db.add(
            Notification(
                user_id=user_id,
                pet_id=pet.id,
                title=f"Meet {pet.name}",
                message=f"A new {pet.type.lower()} is now available for adoption.",
            )
        )
