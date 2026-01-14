import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Table, Column, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel

from .base import metadata


# ENUM do banco
class MediaType(str, enum.Enum):
    GENERAL = "general"
    VIDEOS = "videos"

class MediaTypeDB(str, enum.Enum):
    GENERAL = "general"
    VIDEOS = "videos"



# Tabela SQLAlchemy
media_table = Table(
    "media",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("event_slug", String, nullable=False),
    Column("media_type", Enum(MediaTypeDB, name="media_types"), nullable=False),
    Column("s3_key", String, nullable=False),
    Column("uploader_id", UUID(as_uuid=True), nullable=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


# ENUM do Pydantic (API)
class MediaType(str, enum.Enum):
    general = "general"
    videos = "videos"


# Schema de retorno da API
class MediaOut(BaseModel):
    id: uuid.UUID
    event_slug: str
    media_type: MediaType
    s3_key: str
    s3_url: str
    uploader_id: Optional[uuid.UUID] = None  # ← CORREÇÃO IMPORTANTE
    created_at: datetime

    class Config:
        from_attributes = True
