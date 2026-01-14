import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.dowload_link import download_links_table
from app.settings import settings

BUCKET_RAW = settings.S3_BUCKET_RAW


async def generate_event_photos_zip_url(slug: str, conn: AsyncSession):
    # 🔐 criar senha aleatória
    password = secrets.token_urlsafe(6)  # 10–12 caracteres seguros

    # 📁 gerar URL do zip
    zip_url = f"{BUCKET_RAW}/{slug}/full_download.zip"

    # ⏳ expira em 1h
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # salvar no postgres
    await conn.execute(
        download_links_table.insert().values(
            slug=slug,
            url=zip_url,
            password=password,
            expires_at=expires_at,
        )
    )
    await conn.commit()

    return zip_url, password, expires_at


