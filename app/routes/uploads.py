from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from typing import List, Optional
import imghdr
import asyncio
import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.photo import photos_table, PhotoResponse
from app.services.db import get_conn
from app.services.storage import put_bytes, get_bucket_raw, presign_get
from app.services.face import index_s3_object, sanitize_key_for_rekognition

router = APIRouter()
MAX_SIZE_MB = 1000
ALLOWED_FORMATS = {"jpeg", "png", "jpg"}


def validate_image_bytes(data: bytes):
    if len(data) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"Arquivo acima de {MAX_SIZE_MB}MB")
    if imghdr.what(None, h=data) not in ALLOWED_FORMATS:
        raise HTTPException(415, "Formato nao suportado (use jpg ou png)")


async def process_file(event_slug: str, uploader_id: Optional[uuid.UUID], file: UploadFile):
    """Processa um unico arquivo: valida, salva no Storage e indexa no Face API."""
    try:
        data = await file.read()
        validate_image_bytes(data)

        original_filename = file.filename or "unknown.jpg"
        sanitized_name = sanitize_key_for_rekognition(original_filename)
        ts = int(time.time())

        image_id = uuid.uuid4()
        unique_filename = f"{ts}-{image_id.hex}-{sanitized_name}"
        s3_key = f"{event_slug}/photos/{unique_filename}"

        bucket = get_bucket_raw()

        # 1. Envia para o Storage
        put_bytes(bucket, s3_key, data, file.content_type or "image/jpeg")

        # 2. Envia para o Face API
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: index_s3_object(event_slug, bucket, s3_key, str(image_id))
        )

        return {"image_id": image_id, "s3_key": s3_key}

    except HTTPException as e:
        print(f"!!!!!!!! ERRO DE VALIDACAO: {file.filename}: {e.detail} !!!!!!!!")
        return None
    except Exception as e:
        print(f"!!!!!!!! ERRO AO PROCESSAR O ARQUIVO {file.filename}: {e} !!!!!!!!")
        return None


@router.post("/{event_slug}/photos", response_model=List[PhotoResponse])
async def upload_photos_batch(
        event_slug: str,
        files: List[UploadFile] = File(...),
        uploader_id: Optional[uuid.UUID] = Query(None),
        db: AsyncSession = Depends(get_conn),
):
    """
    Upload de fotos em lote.
    - Se 'uploader_id' for informado, e upload de fotografo.
    - Se for None, e upload de admin.
    """

    # Processa todos os arquivos em paralelo
    tasks = [process_file(event_slug, uploader_id, file) for file in files]
    upload_results = await asyncio.gather(*tasks)

    # Filtra apenas os uploads que tiveram sucesso
    successful_uploads = [res for res in upload_results if res]
    if not successful_uploads:
        return []

    # Prepara os dados para inserir no banco
    photos_to_insert = []
    for res in successful_uploads:
        photos_to_insert.append({
            "id": res["image_id"],
            "uploader_id": uploader_id,
            "event_slug": event_slug,
            "s3_key": res["s3_key"],
            "s3_url": None,
            "status": "active",
        })

    # Insere os novos registros no banco
    stmt = photos_table.insert().values(photos_to_insert)
    await db.execute(stmt)

    # Busca os dados que acabamos de inserir para retornar
    photo_ids = [p["id"] for p in photos_to_insert]
    query = select(photos_table).where(photos_table.c.id.in_(photo_ids))
    result = await db.execute(query)

    await db.commit()

    newly_created_photos = result.all()

    bucket = get_bucket_raw()
    response_data = []
    for photo_row in newly_created_photos:
        photo_dict = dict(photo_row._mapping)
        photo_dict["s3_url"] = presign_get(bucket, photo_dict["s3_key"])
        response_data.append(photo_dict)

    return response_data
