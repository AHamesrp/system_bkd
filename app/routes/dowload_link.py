from datetime import datetime, timezone

from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dowload_link import download_links_table
from app.services.db import get_conn

router = APIRouter()


# -----------------------------
# POST /validate
# -----------------------------
@router.post("/validate")
async def validate_download_request(
    slug: str,
    password: str,
    conn: AsyncSession = Depends(get_conn)
):
    stmt = (
        select(download_links_table)
        .where(download_links_table.c.slug == slug)
    )

    result = await conn.execute(stmt)
    link = result.mappings().first()

    if not link:
        raise HTTPException(404, "Link não encontrado.")

    if datetime.now(timezone.utc) > link["expires_at"]:
        raise HTTPException(410, "Este link já expirou.")

    if link["password"] != password:
        raise HTTPException(401, "Senha incorreta.")

    return {
        "download_url": link["url"],
        "slug": slug
    }


# -----------------------------
# GET /downloads/start
# -----------------------------
@router.get("/downloads/start")
async def start_download(
    slug: str,
    password: str,
    conn: AsyncSession = Depends(get_conn)
):
    stmt = (
        select(download_links_table)
        .where(download_links_table.c.slug == slug)
    )

    result = await conn.execute(stmt)
    link = result.mappings().first()

    if not link:
        raise HTTPException(404, "Link não encontrado.")

    if link["password"] != password:
        raise HTTPException(401, "Senha incorreta.")

    if datetime.now(timezone.utc) > link["expires_at"]:
        raise HTTPException(410, "Link expirado.")

    return {"url": link["url"]}
