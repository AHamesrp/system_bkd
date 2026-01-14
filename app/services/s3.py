import io
import mimetypes
import uuid
import time
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from ..settings import settings

# --- Configuração base ---
s3 = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    config=Config(signature_version="s3v4"),
)

BUCKET_RAW = settings.S3_BUCKET_RAW
EXPIRE = settings.PRESIGNED_EXPIRE_SECONDS


# --- Função de upload robusta ---
def put_bytes(bucket: str, key: str, data: bytes, content_type="application/octet-stream"):
    """Faz upload seguro (inclusive de vídeos grandes) para o S3."""
    try:
        extra_args = {"ContentType": content_type or "application/octet-stream"}

        # ⚙️ Só adiciona encriptação se realmente for necessária
        if getattr(settings, "ENABLE_KMS", False):
            extra_args["ServerSideEncryption"] = "aws:kms"

        s3.upload_fileobj(io.BytesIO(data), bucket, key, ExtraArgs=extra_args)

        print(f"[S3] ✅ Upload realizado: s3://{bucket}/{key} ({len(data)} bytes)")
    except (BotoCoreError, ClientError) as e:
        print(f"[S3] ❌ Erro ao enviar {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao enviar {key}: {e}")
    except Exception as e:
        print(f"[S3] ❌ Erro inesperado: {e}")
        raise


# --- Funções auxiliares ---
def presign_get(bucket: str, key: str, expires: int = EXPIRE) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


def presign_put(bucket: str, key: str, content_type: str, expires: int = EXPIRE) -> str:
    return s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires,
    )


def guess_ext(content_type: str) -> str:
    ext = mimetypes.guess_extension(content_type) or ""
    return ".jpg" if ext == ".jpe" else ext


def make_object_key(event_slug: str, original_name: str) -> str:
    ts = int(time.time())
    return f"{event_slug}/photos/{ts}-{uuid.uuid4().hex}-{original_name}"


def list_keys_in_prefix(bucket: str, prefix: str) -> list[str]:
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
    except (BotoCoreError, ClientError) as e:
        print(f"[S3] ⚠️ Erro ao listar prefixo {prefix}: {e}")
    return keys


async def list_s3_files(prefix: str, bucket: str = BUCKET_RAW):
    """Lista arquivos do S3 (útil pra debug ou APIs públicas)."""
    items = []
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            url = f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            items.append({"key": key.split('/')[-1], "url": url})
    except (BotoCoreError, ClientError) as e:
        print(f"[S3] ⚠️ Erro ao listar arquivos do prefixo {prefix}: {e}")
    return items

def delete_object(bucket: str, key: str) -> None:
    """
    Remove o objeto do S3. Lança HTTPException(500) em caso de erro fatal.
    """
    try:
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"[S3] 🗑️ Removido: s3://{bucket}/{key}")
    except (BotoCoreError, ClientError) as e:
        # Loga e lança para o caller decidir como tratar
        print(f"[S3] ❌ Falha ao apagar s3://{bucket}/{key}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao apagar arquivo no S3: {e}")
    except Exception as e:
        print(f"[S3] ❌ Erro inesperado ao apagar s3://{bucket}/{key}: {e}")
        raise HTTPException(status_code=500, detail="Erro inesperado ao apagar arquivo no S3")