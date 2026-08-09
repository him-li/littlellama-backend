"""Idempotent production demo data for Little Llama."""

import uuid

from app.database import SessionLocal
from app.models import Pet

DEMO_PETS = (
    {
        "id": "10000000-0000-4000-8000-000000000001",
        "type": "Dog",
        "name": "Sir Barks-a-Lot",
        "adoption_status": "Available",
        "height": 42.0,
        "weight": 14.5,
        "color": "Distinguished beige",
        "bio": (
            "A self-appointed neighborhood spokesperson. Has many opinions about "
            "delivery scooters and refuses to disclose his tax returns."
        ),
        "hypoallergenic": False,
        "dietary_restrictions": None,
        "breed": "Executive Retriever",
        "picture": "https://images.unsplash.com/photo-1561037404-61cd46aa615b?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "id": "10000000-0000-4000-8000-000000000002",
        "type": "Cat",
        "name": "Chairman Meow",
        "adoption_status": "Available",
        "height": 24.0,
        "weight": 4.1,
        "color": "Boardroom grey",
        "bio": (
            "Runs every meeting from inside a cardboard box. Promises to improve "
            "productivity by pushing all pens onto the floor."
        ),
        "hypoallergenic": False,
        "dietary_restrictions": "Only accepts snacks presented as quarterly bonuses",
        "breed": "Corporate Shorthair",
        "picture": "https://cataas.com/cat/says/CEO?fontSize=56&fontColor=white",
    },
    {
        "id": "10000000-0000-4000-8000-000000000003",
        "type": "Dog",
        "name": "Bark Obama",
        "adoption_status": "Available",
        "height": 35.0,
        "weight": 10.2,
        "color": "Presidential brown",
        "bio": (
            "Campaign platform: more parks, fewer baths, and a treat in every pocket. "
            "Polling extremely well among mail carriers."
        ),
        "hypoallergenic": False,
        "dietary_restrictions": None,
        "breed": "Democratic Terrier",
        "picture": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "id": "10000000-0000-4000-8000-000000000004",
        "type": "Cat",
        "name": "Purrlock Holmes",
        "adoption_status": "Available",
        "height": 26.0,
        "weight": 4.8,
        "color": "Mystery orange",
        "bio": (
            "Solves crimes nobody reported. The missing tuna was an inside job; "
            "the suspect is currently licking the evidence."
        ),
        "hypoallergenic": False,
        "dietary_restrictions": None,
        "breed": "Consulting Detective Shorthair",
        "picture": "https://cataas.com/cat/says/ELEMENTARY?fontSize=48&fontColor=white",
    },
    {
        "id": "10000000-0000-4000-8000-000000000005",
        "type": "Dog",
        "name": "Mary Puppins",
        "adoption_status": "Fostered",
        "height": 48.0,
        "weight": 18.0,
        "color": "Practically perfect cream",
        "bio": (
            "Arrives whenever the east wind blows, organizes the toy basket, then eats "
            "the measuring tape. Supercalifragilisticexpiali-dog-cious."
        ),
        "hypoallergenic": False,
        "dietary_restrictions": "One spoonful of treats helps the medicine go down",
        "breed": "Magical Nanny Mix",
        "picture": "https://images.unsplash.com/photo-1529665253569-6d01c0eaf7b6?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "id": "10000000-0000-4000-8000-000000000006",
        "type": "Cat",
        "name": "Catrick Swayze",
        "adoption_status": "Available",
        "height": 23.0,
        "weight": 3.9,
        "color": "Dirty Dancing tuxedo",
        "bio": (
            "Nobody puts this kitty in a corner. Special skills include dramatic "
            "entrances and knocking pottery off the wheel."
        ),
        "hypoallergenic": False,
        "dietary_restrictions": None,
        "breed": "Hollywood Shorthair",
        "picture": "https://cataas.com/cat/says/NOBODY%20PUTS%20ME%20IN%20A%20CORNER?fontSize=34&fontColor=white",
    },
)


def seed_demo_data() -> int:
    """Create or synchronize the six seed-owned demo pets."""
    created = 0
    with SessionLocal() as db:
        for item in DEMO_PETS:
            pet_id = uuid.UUID(item["id"])
            pet = db.get(Pet, pet_id)
            if pet is None:
                db.add(Pet(**{**item, "id": pet_id}))
                created += 1
            else:
                for field, value in item.items():
                    if field != "id":
                        setattr(pet, field, value)
        db.commit()
    return created


if __name__ == "__main__":
    print(f"Demo seed complete: {seed_demo_data()} pet(s) created")
