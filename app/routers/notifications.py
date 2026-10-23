import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DbSession
from app.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


def payload(item: Notification) -> dict:
    return {
        "id": item.id,
        "pet_id": item.pet_id,
        "title": item.title,
        "message": item.message,
        "kind": "pet.created" if item.pet_id else "general",
        "pet_name": item.title.removeprefix("Meet ") if item.pet_id else None,
        "read": item.read_at is not None,
        "created_at": item.created_at,
    }


@router.get("")
def list_notifications(current: CurrentUser, db: DbSession) -> list[dict]:
    items = db.scalars(
        select(Notification)
        .where(Notification.user_id == current.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    ).all()
    return [payload(item) for item in items]


@router.get("/unread-count")
def unread_count(current: CurrentUser, db: DbSession) -> dict[str, int]:
    count = (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == current.id, Notification.read_at.is_(None))
        )
        or 0
    )
    return {"count": count}


@router.put("/{notification_id}/read")
def mark_read(notification_id: uuid.UUID, current: CurrentUser, db: DbSession) -> dict:
    item = db.get(Notification, notification_id)
    if item is None or item.user_id != current.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    item.read_at = datetime.now(UTC)
    db.commit()
    return payload(item)


@router.put("/read-all")
def mark_all_read(current: CurrentUser, db: DbSession) -> dict[str, str]:
    for item in db.scalars(
        select(Notification).where(
            Notification.user_id == current.id, Notification.read_at.is_(None)
        )
    ):
        item.read_at = datetime.now(UTC)
    db.commit()
    return {"message": "Notifications marked as read"}
