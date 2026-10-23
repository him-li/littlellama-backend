"""Insert persistent demo users, pets, and relationships once."""

import uuid
from datetime import UTC, datetime

import bcrypt
import sqlalchemy as sa
from alembic import op

revision = "20260810_02"
down_revision = "20260809_01"
branch_labels = None
depends_on = None

DEMO_USER_IDS = (
    uuid.UUID("20000000-0000-4000-8000-000000000001"),
    uuid.UUID("20000000-0000-4000-8000-000000000002"),
)
DEMO_PET_IDS = tuple(uuid.UUID(f"10000000-0000-4000-8000-{index:012d}") for index in range(1, 7))
DEMO_LINK_IDS = (
    uuid.UUID("30000000-0000-4000-8000-000000000001"),
    uuid.UUID("30000000-0000-4000-8000-000000000002"),
    uuid.UUID("30000000-0000-4000-8000-000000000003"),
)


users = sa.table(
    "users",
    sa.column("id", sa.Uuid()),
    sa.column("firstname", sa.String()),
    sa.column("lastname", sa.String()),
    sa.column("email", sa.String()),
    sa.column("phone", sa.String()),
    sa.column("password", sa.String()),
    sa.column("bio", sa.Text()),
    sa.column("admin", sa.Boolean()),
    sa.column("created_at", sa.DateTime(timezone=True)),
)

pets = sa.table(
    "pets",
    sa.column("id", sa.Uuid()),
    sa.column("type", sa.String()),
    sa.column("name", sa.String()),
    sa.column("adoption_status", sa.String()),
    sa.column("height", sa.Float()),
    sa.column("weight", sa.Float()),
    sa.column("color", sa.String()),
    sa.column("bio", sa.Text()),
    sa.column("hypoallergenic", sa.Boolean()),
    sa.column("dietary_restrictions", sa.Text()),
    sa.column("breed", sa.String()),
    sa.column("picture", sa.Text()),
    sa.column("taken_by_user_id", sa.Uuid()),
    sa.column("created_at", sa.DateTime(timezone=True)),
)

pet_users = sa.table(
    "pets_users",
    sa.column("id", sa.Uuid()),
    sa.column("pet_id", sa.Uuid()),
    sa.column("user_id", sa.Uuid()),
    sa.column("saved", sa.Boolean()),
)


def _demo_users(now: datetime) -> list[dict]:
    password = bcrypt.hashpw(b"LittleLlamaDemo!", bcrypt.gensalt()).decode()
    return [
        {
            "id": DEMO_USER_IDS[0],
            "firstname": "Alex",
            "lastname": "Levi",
            "email": "alex.demo@littlellama.pet",
            "phone": "+972-50-555-0101",
            "password": password,
            "bio": "Weekend hiker and first-time dog adopter from Tel Aviv.",
            "admin": False,
            "created_at": now,
        },
        {
            "id": DEMO_USER_IDS[1],
            "firstname": "Maya",
            "lastname": "Cohen",
            "email": "maya.demo@littlellama.pet",
            "phone": "+972-50-555-0102",
            "password": password,
            "bio": "Experienced foster volunteer with a very sunny balcony.",
            "admin": False,
            "created_at": now,
        },
    ]


def _demo_pets(now: datetime) -> list[dict]:
    common = {"hypoallergenic": False, "dietary_restrictions": None, "created_at": now}
    return [
        {
            **common,
            "id": DEMO_PET_IDS[0],
            "type": "Dog",
            "name": "Milo",
            "adoption_status": "Adopted",
            "height": 42.0,
            "weight": 14.5,
            "color": "Golden",
            "bio": "Milo is affectionate, curious, and happiest on a long neighborhood walk.",
            "breed": "Mixed Retriever",
            "picture": "https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=1200&q=85",
            "taken_by_user_id": DEMO_USER_IDS[0],
        },
        {
            **common,
            "id": DEMO_PET_IDS[1],
            "type": "Cat",
            "name": "Luna",
            "adoption_status": "Fostered",
            "height": 24.0,
            "weight": 4.1,
            "color": "Grey tabby",
            "bio": "Luna is gentle and observant, and loves quiet company by a sunny window.",
            "breed": "Domestic Shorthair",
            "picture": "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?auto=format&fit=crop&w=1200&q=85",
            "taken_by_user_id": DEMO_USER_IDS[1],
        },
        {
            **common,
            "id": DEMO_PET_IDS[2],
            "type": "Dog",
            "name": "Nala",
            "adoption_status": "Available",
            "height": 35.0,
            "weight": 10.2,
            "color": "White and brown",
            "bio": "Nala is clever, friendly, and learns new routines very quickly.",
            "breed": "Jack Russell Mix",
            "picture": "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?auto=format&fit=crop&w=1200&q=85",
            "taken_by_user_id": None,
        },
        {
            **common,
            "id": DEMO_PET_IDS[3],
            "type": "Cat",
            "name": "Simba",
            "adoption_status": "Available",
            "height": 26.0,
            "weight": 4.8,
            "color": "Orange tabby",
            "bio": "Simba is playful, sociable, and always ready to explore a new cardboard box.",
            "breed": "Domestic Shorthair",
            "picture": "https://images.unsplash.com/photo-1574158622682-e40e69881006?auto=format&fit=crop&w=1200&q=85",
            "taken_by_user_id": None,
        },
        {
            **common,
            "id": DEMO_PET_IDS[4],
            "type": "Dog",
            "name": "Coco",
            "adoption_status": "Available",
            "height": 48.0,
            "weight": 18.0,
            "color": "Cream",
            "bio": "Coco is calm around children and would thrive in an active home.",
            "breed": "Labrador Mix",
            "picture": "https://images.unsplash.com/photo-1530281700549-e82e7bf110d6?auto=format&fit=crop&w=1200&q=85",
            "taken_by_user_id": None,
        },
        {
            **common,
            "id": DEMO_PET_IDS[5],
            "type": "Cat",
            "name": "Pepper",
            "adoption_status": "Available",
            "height": 23.0,
            "weight": 3.9,
            "color": "Black and white",
            "bio": "Pepper is tidy, relaxed, and happiest beside someone reading on the sofa.",
            "breed": "Domestic Shorthair",
            "picture": "https://images.unsplash.com/photo-1495360010541-f48722b34f7d?auto=format&fit=crop&w=1200&q=85",
            "taken_by_user_id": None,
        },
    ]


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(UTC)

    existing_user_ids = set(connection.execute(sa.select(users.c.id)).scalars())
    for user in _demo_users(now):
        if user["id"] not in existing_user_ids:
            connection.execute(users.insert().values(**user))

    existing_pet_ids = set(connection.execute(sa.select(pets.c.id)).scalars())
    for pet in _demo_pets(now):
        if pet["id"] in existing_pet_ids:
            values = {key: value for key, value in pet.items() if key not in {"id", "created_at"}}
            connection.execute(pets.update().where(pets.c.id == pet["id"]).values(**values))
        else:
            connection.execute(pets.insert().values(**pet))

    links = [
        {
            "id": DEMO_LINK_IDS[0],
            "pet_id": DEMO_PET_IDS[2],
            "user_id": DEMO_USER_IDS[0],
            "saved": True,
        },
        {
            "id": DEMO_LINK_IDS[1],
            "pet_id": DEMO_PET_IDS[3],
            "user_id": DEMO_USER_IDS[1],
            "saved": True,
        },
        {
            "id": DEMO_LINK_IDS[2],
            "pet_id": DEMO_PET_IDS[5],
            "user_id": DEMO_USER_IDS[1],
            "saved": True,
        },
    ]
    existing_link_ids = set(connection.execute(sa.select(pet_users.c.id)).scalars())
    for link in links:
        if link["id"] not in existing_link_ids:
            connection.execute(pet_users.insert().values(**link))


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(pet_users.delete().where(pet_users.c.id.in_(DEMO_LINK_IDS)))
    connection.execute(pets.delete().where(pets.c.id.in_(DEMO_PET_IDS)))
    connection.execute(users.delete().where(users.c.id.in_(DEMO_USER_IDS)))
