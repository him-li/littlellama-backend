import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import DbSession, OptionalUser, SupportUser
from app.models import ContactInquiry
from app.schemas import ContactInquiryCreate, InquiryStatusUpdate
from app.services import record_activity

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_inquiry(payload: ContactInquiryCreate, current: OptionalUser, db: DbSession) -> dict:
    item = ContactInquiry(user_id=current.id if current else None, **payload.model_dump())
    db.add(item)
    db.flush()
    record_activity(
        db, "inquiry.created", "inquiry", item.id, f"New inquiry: {item.subject}", actor=current
    )
    db.commit()
    db.refresh(item)
    return inquiry_payload(item)


def inquiry_payload(item: ContactInquiry) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "name": item.name,
        "email": item.email,
        "subject": item.subject,
        "message": item.message,
        "status": item.status,
        "created_at": item.created_at,
    }


@router.get("")
def list_inquiries(_: SupportUser, db: DbSession) -> list[dict]:
    return [
        inquiry_payload(item)
        for item in db.scalars(
            select(ContactInquiry).order_by(ContactInquiry.created_at.desc())
        ).all()
    ]


@router.put("/{inquiry_id}")
def update_inquiry(
    inquiry_id: uuid.UUID, payload: InquiryStatusUpdate, current: SupportUser, db: DbSession
) -> dict:
    item = db.get(ContactInquiry, inquiry_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inquiry not found")
    item.status = payload.status
    record_activity(
        db,
        "inquiry.status_changed",
        "inquiry",
        item.id,
        f"Inquiry marked {payload.status}",
        actor=current,
    )
    db.commit()
    return inquiry_payload(item)
