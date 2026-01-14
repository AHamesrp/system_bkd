from sqlalchemy import Table, Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
import uuid
from .base import metadata


# --- Definição da tabela ---
photos_table = Table(
    "photos",
    metadata,
    Column("id", SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("uploader_id", SQLAlchemyUUID(as_uuid=True), ForeignKey("users.id"), nullable=True),  # ✅ Agora pode ser NULL
    Column("event_slug", String, nullable=False),
    Column("s3_key", String, nullable=False),
    Column("s3_url", String, nullable=True),
    Column("status", String, nullable=False, default="active"),
    Column("created_at", DateTime, default=datetime.utcnow),
)


# --- Schemas Pydantic ---
class PhotoIn(BaseModel):
    event_slug: str
    s3_key: str
    s3_url: HttpUrl
    uploader_id: Optional[uuid.UUID] = None  # ✅ Torna opcional


class PhotoUpdate(BaseModel):
    status: Optional[str] = None


class PhotoResponse(BaseModel):
    id: uuid.UUID
    uploader_id: Optional[uuid.UUID] = None  # ✅ Pode ser null
    event_slug: str
    s3_key: str
    s3_url: HttpUrl
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {uuid.UUID: lambda u: str(u)}
