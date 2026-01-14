from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.event import CreateEventIn, EventOut
from app.services.db import get_conn
from app.services.events import create_event as create_event_service
from app.services.events import get_event_by_slug as get_event_by_slug_service
from app.services.events import list_events
from typing import List
router = APIRouter()


@router.get("/{slug}", response_model=EventOut)
async def get_event(slug: str, conn: AsyncSession = Depends(get_conn)):
    event = await get_event_by_slug_service(conn, slug)
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return event

# Listar eventos
@router.get("", response_model=List[EventOut])
async def events_list(conn: AsyncSession = Depends(get_conn)):
    return await list_events(conn)
