from typing import Any

from app.models import Pet, PetUser, User


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
    }
    if full:
        data["owned_pets"] = [pet_payload(pet) for pet in user.pets]
        data["saved_pets"] = [pet_payload(link.pet, link) for link in user.saved_pet_links]
    return data
