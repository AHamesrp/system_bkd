"""recreate missing tables photos and comments

Revision ID: e5dcc058569c
Revises: 47ed9c8d4dce
Create Date: 2025-11-24 18:41:30.423539+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5dcc058569c'
down_revision: Union[str, None] = '47ed9c8d4dce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

from sqlalchemy.dialects import postgresql # Necessário para UUID


def upgrade() -> None:
    # Recriação da tabela "comments"
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_slug", sa.String(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Recriação da tabela "photos"
    op.create_table(
        "photos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()")
        ),
        # Usando nullable=True para uploader_id, que foi o estado final da migração b7670fecd4e1
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_slug", sa.String(), nullable=False),
        sa.Column("s3_key", sa.String(), nullable=False),
        sa.Column("s3_url", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="'active'"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Desfazendo a criação das tabelas
    op.drop_table("photos")
    op.drop_table("comments")
