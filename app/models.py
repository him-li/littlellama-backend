import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    firstname: Mapped[str] = mapped_column(String(100))
    lastname: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(40))
    password: Mapped[str] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    pets: Mapped[list["Pet"]] = relationship(back_populates="owner")
    saved_pet_links: Mapped[list["PetUser"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(100), index=True)
    adoption_status: Mapped[str] = mapped_column(String(30), default="Available")
    height: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)
    color: Mapped[str] = mapped_column(String(100))
    bio: Mapped[str] = mapped_column(Text)
    hypoallergenic: Mapped[bool] = mapped_column(Boolean, default=False)
    dietary_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    breed: Mapped[str] = mapped_column(String(120), index=True)
    picture: Mapped[str] = mapped_column(Text)
    taken_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    owner: Mapped[User | None] = relationship(back_populates="pets")
    saved_by_links: Mapped[list["PetUser"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )


class PetUser(Base):
    __tablename__ = "pets_users"
    __table_args__ = (UniqueConstraint("pet_id", "user_id", name="uq_pet_user"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    saved: Mapped[bool] = mapped_column(Boolean, default=True)

    pet: Mapped[Pet] = relationship(back_populates="saved_by_links")
    user: Mapped[User] = relationship(back_populates="saved_pet_links")
