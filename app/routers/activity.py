from fastapi import APIRouter, Query
from sqlalchemy import select

from app.dependencies import AdminUser, DbSession
from app.models import ActivityEvent
from app.schemas import ActivityOut

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityOut])
def get_activity(
    _: AdminUser, db: DbSession, limit: int = Query(50, ge=1, le=100)
) -> list[ActivityEvent]:
    return list(
        db.scalars(select(ActivityEvent).order_by(ActivityEvent.created_at.desc()).limit(limit))
    )
