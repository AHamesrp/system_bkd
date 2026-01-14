"""Make uploader_id nullable on photos table

Revision ID: b7670fecd4e1
Revises: e86006d48d85
Create Date: 2025-11-10 20:04:34.646427+00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7670fecd4e1'
down_revision = 'e86006d48d85'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('photos', 'uploader_id', nullable=True)


def downgrade() -> None:
    op.alter_column('photos' , 'uploader_id', nullable=True)


