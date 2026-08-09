"""Idempotent production demo data for Little Llama."""

import uuid

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Pet

DEMO_PETS = (
    {
        "id": "10000000-0000-4000-8000-000000000001",
        "type": "Dog",
        "name": "Milo",
        "adoption_status": "Available",
        "height": 42.0,
        "weight": 14.5,
        "color": "Golden",
        "bio": "Milo is an affectionate, curious dog who loves long walks and quiet naps.",
        "hypoallergenic": False,
        "dietary_restrictions": None,
        "breed": "Mixed Retriever",
        "picture": "https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "id": "10000000-0000-4000-8000-000000000002",
        "type": "Cat",
        "name": "Luna",
        "adoption_status": "Available",
        "height": 24.0,
        "weight": 4.1,
        "color": "Grey tabby",
        "bio": "Luna is gentle and observant. She enjoys sunny windows and patient company.",
        "hypoallergenic": False,
        "dietary_restrictions": "Grain-free food",
        "breed": "Domestic Shorthair",
        "picture": "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "id": "10000000-0000-4000-8000-000000000003",
        "type": "Dog",
        "name": "Nala",
        "adoption_status": "Available",
        "height": 35.0,
        "weight": 10.2,
        "color": "White and brown",
        "bio": "Nala is a clever young dog who learns quickly and gets along well with families.",
        "hypoallergenic": False,
        "dietary_restrictions": None,
        "breed": "Jack Russell Mix",
        "picture": "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "id": "10000000-0000-4000-8000-000000000004",
        "type": "Cat",
        "name": "Simba",
        "adoption_status": "Available",
        "height": 26.0,
        "weight": 4.8,
        "color": "Orange tabby",
        "bio": "Simba is playful, sociable, and always ready to investigate a cardboard box.",
        "hypoallergenic": False,
        "dietary_restrictions": None,
        "breed": "Domestic Shorthair",
        "picture": "https://images.unsplash.com/photo-1574158622682-e40e69881006?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "id": "10000000-0000-4000-8000-000000000005",
        "type": "Dog",
        "name": "Coco",
        "adoption_status": "Fostered",
        "height": 48.0,
        "weight": 18.0,
        "color": "Cream",
        "bio": "Coco is currently thriving in foster care and is ready for a permanent home.",
        "hypoallergenic": False,
        "dietary_restrictions": "Sensitive-stomach formula",
        "breed": "Labrador Mix",
        "picture": "https://images.unsplash.com/photo-1530281700549-e82e7bf110d6?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "id": "10000000-0000-4000-8000-000000000006",
        "type": "Cat",
        "name": "Pepper",
        "adoption_status": "Available",
        "height": 23.0,
        "weight": 3.9,
        "color": "Black and white",
        "bio": "Pepper is calm, tidy, and happiest beside someone reading on the sofa.",
        "hypoallergenic": False,
        "dietary_restrictions": None,
        "breed": "Domestic Shorthair",
        "picture": "https://images.unsplash.com/photo-1495360010541-f48722b34f7d?auto=format&fit=crop&w=1200&q=85",
    },
)


def seed_demo_data() -> int:
    """Insert missing demo pets and return the number created."""
    created = 0
    with SessionLocal() as db:
        existing_ids = set(
            db.scalars(
                select(Pet.id).where(
                    Pet.id.in_([uuid.UUID(item["id"]) for item in DEMO_PETS])
                )
            )
        )
        for item in DEMO_PETS:
            pet_id = uuid.UUID(item["id"])
            if pet_id not in existing_ids:
                db.add(Pet(**{**item, "id": pet_id}))
                created += 1
        db.commit()
    return created


if __name__ == "__main__":
    print(f"Demo seed complete: {seed_demo_data()} pet(s) created")
