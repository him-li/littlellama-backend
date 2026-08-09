from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Pet
from app.seed import DEMO_PETS, seed_demo_data


def test_demo_seed_is_idempotent() -> None:
    assert seed_demo_data() == len(DEMO_PETS)
    assert seed_demo_data() == 0
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Pet)) == len(DEMO_PETS)
