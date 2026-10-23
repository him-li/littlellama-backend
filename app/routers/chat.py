import uuid
from collections import defaultdict
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession
from app.models import ChatMessage, Conversation, User
from app.schemas import ChatMessageCreate
from app.security import decode_access_token

router = APIRouter(prefix="/chat", tags=["chat"])


def can_access(conversation: Conversation, user: User) -> bool:
    return conversation.user_id == user.id or user.admin or user.role in {"admin", "support"}


def message_payload(message: ChatMessage) -> dict:
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "sender_id": str(message.sender_id),
        "body": message.body,
        "created_at": message.created_at.isoformat(),
    }


def conversation_payload(item: Conversation) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "assigned_support_id": item.assigned_support_id,
        "status": item.status,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "messages": [message_payload(message) for message in item.messages],
    }


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def open_conversation(current: CurrentUser, db: DbSession) -> dict:
    item = db.scalar(
        select(Conversation)
        .where(Conversation.user_id == current.id, Conversation.status == "open")
        .options(selectinload(Conversation.messages))
    )
    if item is None:
        item = Conversation(user_id=current.id)
        db.add(item)
        db.commit()
        db.refresh(item)
    return conversation_payload(item)


@router.get("/conversations")
def list_conversations(current: CurrentUser, db: DbSession) -> list[dict]:
    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
    )
    if not current.admin and current.role not in {"admin", "support"}:
        query = query.where(Conversation.user_id == current.id)
    return [conversation_payload(item) for item in db.scalars(query).unique().all()]


@router.post("/conversations/{conversation_id}/messages")
def post_message(
    conversation_id: uuid.UUID, payload: ChatMessageCreate, current: CurrentUser, db: DbSession
) -> dict:
    item = db.get(Conversation, conversation_id)
    if item is None or not can_access(item, current):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    message = ChatMessage(conversation_id=item.id, sender_id=current.id, body=payload.body)
    item.updated_at = datetime.now(UTC)
    if current.admin or current.role in {"admin", "support"}:
        item.assigned_support_id = current.id
    db.add(message)
    db.commit()
    db.refresh(message)
    return message_payload(message)


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, conversation_id: uuid.UUID, socket: WebSocket) -> None:
        await socket.accept()
        self.connections[conversation_id].add(socket)

    def disconnect(self, conversation_id: uuid.UUID, socket: WebSocket) -> None:
        self.connections[conversation_id].discard(socket)

    async def broadcast(self, conversation_id: uuid.UUID, payload: dict) -> None:
        stale = []
        for socket in self.connections[conversation_id]:
            try:
                await socket.send_json(payload)
            except RuntimeError:
                stale.append(socket)
        for socket in stale:
            self.disconnect(conversation_id, socket)


manager = ConnectionManager()


@router.websocket("/ws/{conversation_id}")
async def chat_socket(
    socket: WebSocket, conversation_id: uuid.UUID, db: DbSession, token: str = Query(...)
) -> None:
    try:
        payload = decode_access_token(token)
        user = db.get(User, uuid.UUID(payload["sub"]))
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        user = None
    conversation = db.get(Conversation, conversation_id)
    if user is None or conversation is None or not can_access(conversation, user):
        await socket.close(code=1008)
        return
    user_id = user.id
    await manager.connect(conversation_id, socket)
    try:
        while True:
            body = (await socket.receive_text()).strip()
            if not body or len(body) > 4000:
                continue
            item = db.get(Conversation, conversation_id)
            message = ChatMessage(conversation_id=conversation_id, sender_id=user_id, body=body)
            item.updated_at = datetime.now(UTC)
            if user.admin or user.role in {"admin", "support"}:
                item.assigned_support_id = user.id
            db.add(message)
            db.commit()
            db.refresh(message)
            outgoing = message_payload(message)
            await manager.broadcast(conversation_id, outgoing)
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, socket)
