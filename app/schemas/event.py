from sqlalchemy import Table, Column, String, Date, Time, Integer
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import date, time  # Import date and time types
from .base import metadata

# Tabela de eventos no banco com os novos campos
events_table = Table(
    "events",
    metadata,
    Column("slug", String, primary_key=True),
    Column("title", String, nullable=False),
    Column("privacy_url", String, nullable=True),
    Column("event_date", Date, nullable=True),
    Column("start_time", Time, nullable=True),
    Column("end_time", Time, nullable=True),
    Column("participants_count", Integer, nullable=True),
)

# --- Schemas Pydantic -------------------

class CreateEventIn(BaseModel):
    """Schema para criar/atualizar um evento."""
    slug: str
    title: str
    privacy_url: Optional[HttpUrl] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    participants_count: Optional[int] = None

class EventOut(BaseModel):
    """Schema para retornar dados de um evento."""
    slug: str
    title: str
    privacy_url: Optional[str] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    participants_count: Optional[int] = None

    class Config:
        from_attributes = True

# ✅ CORREÇÃO: Adicione este schema que estava faltando
class UpdateEventIn(BaseModel):
    """Schema para ATUALIZAR um evento. Todos os campos são opcionais."""
    title: Optional[str] = None
    privacy_url: Optional[HttpUrl] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    participants_count: Optional[int] = None