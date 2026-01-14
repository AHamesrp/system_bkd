# Arquivo: /app/services/downloads.py

import io
import zipfile
from datetime import datetime

# Importe as funções e o cliente do seu arquivo utilitário de S3
from . import s3
from ..settings import settings


async def generate_event_photos_zip_url(event_slug: str) -> str:
    """
    Gera um arquivo .zip com todas as fotos de um evento, faz upload para o S3,
    e retorna uma URL de download pré-assinada.
    """
    # 1. Listar todas as chaves de fotos diretamente do S3 usando o prefixo do evento.
    prefix = f"{event_slug}/photos/"
    photo_keys = s3.list_keys_in_prefix(bucket=settings.S3_BUCKET_RAW, prefix=prefix)

    if not photo_keys:
        raise ValueError("Nenhuma foto encontrada para este evento.")

    # 2. Criar um arquivo .zip em memória
    in_memory_zip = io.BytesIO()
    with zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for photo_key in photo_keys:
            try:
                # Baixa cada foto do S3
                response = s3.s3.get_object(Bucket=settings.S3_BUCKET_RAW, Key=photo_key)
                photo_data = response['Body'].read()

                # Extrai o nome do arquivo da chave S3 para usar no zip
                file_name = photo_key.split('/')[-1]

                # Adiciona a foto ao zip (se não for uma pasta)
                if file_name:
                    zf.writestr(file_name, photo_data)

            except s3.s3.exceptions.NoSuchKey:
                print(f"Aviso: A foto com a chave '{photo_key}' não foi encontrada no S3.")
                continue

    in_memory_zip.seek(0)

    # 3. Fazer o upload do .zip para o S3
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    zip_key = f"zips/{event_slug}-{timestamp}.zip"

    s3.put_bytes(
        bucket=settings.S3_BUCKET_RAW,
        key=zip_key,
        data=in_memory_zip.getvalue(),
        content_type="application/zip"
    )

    # 4. Gerar um link de download pré-assinado
    presigned_url = s3.presign_get(
        bucket=settings.S3_BUCKET_RAW,
        key=zip_key
    )

    return presigned_url