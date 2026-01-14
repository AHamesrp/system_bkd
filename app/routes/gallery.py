from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.storage import list_keys_in_prefix, presign_get, get_bucket_raw
from app.services.db import get_conn

router = APIRouter()

@router.get("/{event_slug}/general")
async def list_general_photos(event_slug: str, conn: AsyncSession = Depends(get_conn)):
    """
    Lista as fotos gerais de um evento e gera URLs pre-assinadas.
    """
    try:
        bucket = get_bucket_raw()
        folder = f"{event_slug}/general/"
        keys = list_keys_in_prefix(bucket, folder)
        files = [{"key": key, "url": presign_get(bucket, key)} for key in keys]
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar fotos: {e}")

@router.get("/{event_slug}/videos")
async def list_event_videos(event_slug: str, conn: AsyncSession = Depends(get_conn)):
    """
    Lista os videos de um evento e gera URLs pre-assinadas.
    """
    try:
        bucket = get_bucket_raw()
        folder = f"{event_slug}/videos/"
        keys = list_keys_in_prefix(bucket, folder)
        files = [{"key": key.split("/")[-1], "url": presign_get(bucket, key)} for key in keys]
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar videos: {e}")
