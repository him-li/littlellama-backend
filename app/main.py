from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.database import SessionLocal
from app.routers import activity, auth, chat, contact, notifications, pets, users
from app.schemas import HealthResponse

settings = get_settings()
app = FastAPI(
    title="Little Llama API",
    description="Pet adoption API for the Little Llama portfolio project.",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(pets.router)
app.include_router(activity.router)
app.include_router(notifications.router)
app.include_router(contact.router)
app.include_router(chat.router)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/ready", response_model=HealthResponse, tags=["operations"])
def readiness() -> HealthResponse:
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return HealthResponse()
