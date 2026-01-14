import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import List, Literal
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

# Import de serviços
from app.services.db import get_conn
from app.services import events as event_service
from app.services import downloads as downloads_service

# Import de schemas e tabelas
from app.schemas.event import CreateEventIn, EventOut, UpdateEventIn, events_table
from app.schemas.metrics import AdminMetricSummary, metrics_table
from app.schemas.dowload_link import download_links_table
from app.schemas.user import users_table, UserOut
from app.security.jwt import require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


# --- SCHEMAS ESPECÍFICOS DA ROTA ---

class DownloadLinkOut(BaseModel):
    """Schema para a resposta da geração de link."""
    url: str

class RawMetricOut(BaseModel):
    """Schema para a resposta da rota de atividade bruta (gráfico)."""
    # ✅ FIX: Adicionado 'upload_media' à lista de tipos permitidos
    type: Literal["search", "register", "download_photo", "upload_media"]
    count: int
    created_at: datetime


# --- ROTAS DE EVENTOS (sem alterações) ---

@router.get("/events", response_model=List[EventOut])
async def list_events(conn: AsyncSession = Depends(get_conn)):
    """Lista todos os eventos cadastrados."""
    result = await conn.execute(select(events_table).order_by(events_table.c.event_date.desc()))
    rows = result.mappings().all()
    return [EventOut.model_validate(row) for row in rows]

@router.post("/events", response_model=EventOut, status_code=201)
async def create_event(payload: CreateEventIn, conn: AsyncSession = Depends(get_conn)):
    """Cria um novo evento."""
    return await event_service.create_event(conn, payload)

@router.patch("/events/{slug}", response_model=EventOut)
async def update_event(slug: str, payload: UpdateEventIn, conn: AsyncSession = Depends(get_conn)):
    """Atualiza um evento existente."""
    updated_event = await event_service.update_event(conn, slug, payload)
    if not updated_event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return updated_event


# --- GERAÇÃO DE LINK PARA DOWNLOAD (sem alterações) ---

# ✅ response_model usa o DownloadLinkOut importado, que contém url, password e expires_at
@router.post("/events/{slug}/generate-download-link", response_model=DownloadLinkOut)
async def generate_download_link(slug: str, conn: AsyncSession = Depends(get_conn)):
    password = secrets.token_hex(3)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    zip_url = await downloads_service.generate_event_photos_zip_url(slug)

    await conn.execute(
        download_links_table.insert().values(
            slug=slug,
            url=zip_url,
            password=password,
            expires_at=expires_at,
        )
    )
    await conn.commit()

    # O retorno deve ser compatível com o schema (DownloadLinkOut)
    return {
        "url": f"https:/moments-floripasquare.com.br/{slug}/download",
        "password": password,
        "expires_at": expires_at,
    }
@router.get("/metrics", response_model=List[AdminMetricSummary])
async def all_aggregated_metrics(conn: AsyncSession = Depends(get_conn)):
    """
    Lista métricas de engajamento agregadas por usuário para TODOS os eventos.
    Usa LEFT JOIN para incluir usuários sem métricas.
    """
    j = users_table.join(
        metrics_table, users_table.c.id == metrics_table.c.user_id, isouter=True
    )
    result = await conn.execute(
        select(
            users_table.c.event_slug,
            users_table.c.name.label("user_name"),
            users_table.c.email,
            users_table.c.instagram,
            users_table.c.whatsapp,
            func.sum(case((metrics_table.c.type == "search", metrics_table.c.count), else_=0)).label("pesquisas"),
            func.sum(case((metrics_table.c.type == "register", metrics_table.c.count), else_=0)).label("cadastros"),
            func.sum(case((metrics_table.c.type == "download_photo", metrics_table.c.count), else_=0)).label("downloads"),
        )
        .select_from(j)
        .group_by(
            users_table.c.event_slug,
            users_table.c.name,
            users_table.c.email,
            users_table.c.instagram,
            users_table.c.whatsapp
        )
        .order_by(users_table.c.event_slug, users_table.c.name)
    )
    return result.mappings().all()

@router.get("/metrics/activity", response_model=List[RawMetricOut])
async def get_raw_activity_metrics(conn: AsyncSession = Depends(get_conn)):
    """
    Retorna uma lista de métricas brutas (não agregadas) para
    alimentar o gráfico de atividade em tempo real no dashboard.
    """
    result = await conn.execute(
        select(
            metrics_table.c.type,
            metrics_table.c.count,
            metrics_table.c.created_at
        )
        .order_by(metrics_table.c.created_at.asc())
    )
    return result.mappings().all()

@router.get("/events/{event_slug}/metrics", response_model=List[AdminMetricSummary])
async def event_metrics_by_slug(event_slug: str, conn: AsyncSession = Depends(get_conn)):
    """
    Lista métricas de engajamento para TODOS os usuários de um evento específico.
    """
    j = users_table.join(
        metrics_table, users_table.c.id == metrics_table.c.user_id, isouter=True
    )
    result = await conn.execute(
        select(
            users_table.c.event_slug,
            users_table.c.name.label("user_name"),
            users_table.c.last_name,
            users_table.c.email,
            users_table.c.instagram,
            users_table.c.whatsapp,
            func.sum(case((metrics_table.c.type == "search", metrics_table.c.count), else_=0)).label("pesquisas"),
            func.sum(case((metrics_table.c.type == "register", metrics_table.c.count), else_=0)).label("cadastros"),
            func.sum(case((metrics_table.c.type == "download_photo", metrics_table.c.count), else_=0)).label("downloads"),
        )
        .select_from(j)
        .where(users_table.c.event_slug == event_slug)
        .group_by(
            users_table.c.event_slug,
            users_table.c.name,
            users_table.c.last_name,
            users_table.c.email,
            users_table.c.instagram,
            users_table.c.whatsapp
        )
        .order_by(users_table.c.name)
    )
    return result.mappings().all()


# --- ROTAS DE USUÁRIOS (sem alterações) ---

@router.get("/users/{event_slug}", response_model=List[UserOut])
async def users_by_event(event_slug: str, conn: AsyncSession = Depends(get_conn)):
    """Lista todos os usuários detalhados de um evento específico."""
    result = await conn.execute(
        select(users_table).where(users_table.c.event_slug == event_slug)
    )
    rows = result.mappings().all()
    return [UserOut.model_validate(row) for row in rows]