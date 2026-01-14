# app/schemas/dowload_link.py (NOVO PADRÃO: sa.Table)

import sqlalchemy as sa
from sqlalchemy import Table, Column, String, Text, DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict
from .base import metadata  # Importa a metadata compartilhada

# --- Definição da tabela usando sa.Table ---
download_links_table = Table(
    "download_links",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("slug", String(255), nullable=False),
    Column("url", Text, nullable=False),
    Column("password", String(255), nullable=False),

    # ⚠️ IMPORTANTE: timezone=True — garante DATETIME WITH TIME ZONE
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


# --- Schemas Pydantic (Sem alteração) ---

class DownloadLinkOut(BaseModel):
    id: int
    slug: str
    url: str
    password: str

    model_config = ConfigDict(from_attributes=True)


class DownloadLinkCreate(BaseModel):
    slug: str
    url: str
    password: str
    expires_at: datetime


class DownloadLinkPublic(BaseModel):
    slug: str
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)