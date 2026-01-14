"""001_INITIAL

Revision ID: d1b5087105a4
Revises: 
Create Date: 2025-09-26 12:26:36.838378+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

# revision identifiers, used by Alembic.
revision = "d1b5087105a4"
down_revision = None
branch_labels = None
depends_on = None

# Enum para roles
class UserRoleEnum(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    PHOTOGRAPHER = "PHOTOGRAPHER"

def upgrade() -> None:

    # --- users ---
    op.create_table(
        "users",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("whatsapp", sa.String(), nullable=True),
        sa.Column("instagram", sa.String(), nullable=True),
        sa.Column("accepted_lgpd", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("event_slug", sa.String(), nullable=True),
        sa.Column(
            "role",
            sa.Enum("USER", "ADMIN", "PHOTOGRAPHER", name="user_roles"),
            nullable=False,
            server_default=sa.text("'USER'")
        ),
    )

    # --- events ---
    op.create_table(
        "events",
        sa.Column("slug", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("privacy_url", sa.String(), nullable=True),
    )

    # --- metrics ---
    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_slug", sa.String(), sa.ForeignKey("events.slug"), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("count", sa.Integer(), server_default="1"),
        sa.Column("data", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- active_sessions ---
    op.create_table(
        "active_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_jti", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # --- token_denylist ---
    op.create_table(
        "token_denylist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jti", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    # dropa as tabelas
    op.drop_table("token_denylist")
    op.drop_table("active_sessions")
    op.drop_table("metrics")
    op.drop_table("events")
    op.drop_table("users")
    # dropa o ENUM apenas se existir
    op.execute("DROP TYPE IF EXISTS user_roles")
