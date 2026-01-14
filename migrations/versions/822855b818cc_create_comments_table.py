"""create comments table

Revision ID: 822855b818cc
Revises: b7670fecd4e1
Create Date: 2025-11-11 23:24:30.256223+00:00

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '822855b818cc'
down_revision: Union[str, None] = 'b7670fecd4e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "comments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_slug", sa.String(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )


def downgrade():
    # Removendo apenas o comando de drop_table
    op.drop_table("comments")