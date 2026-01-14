"""add photos table

Revision ID: e86006d48d85
Revises: ac18f0285bd3
Create Date: 2025-10-29 22:48:21.711558+00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e86006d48d85'
down_revision = 'ac18f0285bd3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "photos",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()")  # PostgreSQL + pgcrypto
        ),
        sa.Column("uploader_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_slug", sa.String(), nullable=False),
        sa.Column("s3_key", sa.String(), nullable=False),
        sa.Column("s3_url", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="'active'"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("photos")
