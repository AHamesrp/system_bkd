from sqlalchemy import Table, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from .base import metadata

comments_table = Table(
    "comments",
    metadata,
    Column("id", SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", SQLAlchemyUUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("event_slug", String, nullable=False),
    Column("comment", Text, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class CommentIn(BaseModel):
    user_id: uuid.UUID
    event_slug: str
    comment: str


class CommentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_slug: str
    comment: str
    created_at: datetime
    user_full_name: Optional[str] = None
    user_instagram: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {uuid.UUID: lambda u: str(u)}
