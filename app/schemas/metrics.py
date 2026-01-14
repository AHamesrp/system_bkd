# app/schemas/metrics.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from .base import metadata
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

metrics_table = sa.Table(
    "metrics",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    sa.Column("event_slug", sa.String, sa.ForeignKey("events.slug"), nullable=True),
    sa.Column("type", sa.String, nullable=False),  # ex: "search", "upload", etc.
    sa.Column("count", sa.Integer, default=1),
    sa.Column("data", JSONB, nullable=True),  # 👈 para guardar payload flexível
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
)


class MetricIn(BaseModel):
    user_id: Optional[str] = None
    event_slug: Optional[str] = None
    type: str
    count: Optional[int] = 1
    data: Optional[Dict[str, Any]] = None  # 👈 metadados extras


class MetricOut(MetricIn):
    id: str
    created_at: str

class AdminMetricSummary(BaseModel):
    event_slug: Optional[str] = None
    user_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None       # Adicionado
    instagram: Optional[str] = None   # Adicionado
    whatsapp: Optional[str] = None    # Adicionado
    pesquisas: int
    cadastros: int
    downloads: int

    class Config:
        from_attributes = True


class DownloadMetricIn(BaseModel):
    event_slug: str
    file_name: str