"""Initial Little Llama schema."""

import sqlalchemy as sa
from alembic import op

revision = "20260809_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("firstname", sa.String(100), nullable=False),
        sa.Column("lastname", sa.String(100), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("bio", sa.Text()),
        sa.Column("admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "pets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("adoption_status", sa.String(30), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("color", sa.String(100), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("hypoallergenic", sa.Boolean(), nullable=False),
        sa.Column("dietary_restrictions", sa.Text()),
        sa.Column("breed", sa.String(120), nullable=False),
        sa.Column("picture", sa.Text(), nullable=False),
        sa.Column("taken_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pets_name", "pets", ["name"])
    op.create_index("ix_pets_breed", "pets", ["breed"])
    op.create_index("ix_pets_taken_by_user_id", "pets", ["taken_by_user_id"])
    op.create_table(
        "pets_users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "pet_id", sa.Uuid(), sa.ForeignKey("pets.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("saved", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("pet_id", "user_id", name="uq_pet_user"),
    )


def downgrade() -> None:
    op.drop_table("pets_users")
    op.drop_table("pets")
    op.drop_table("users")
