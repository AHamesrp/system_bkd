"""
azure_blob.py - Serviço de Storage com Azure Blob Storage

Este módulo substitui o s3.py (AWS) mantendo a mesma interface
de funções para garantir compatibilidade com o restante do código.

Mapeamento AWS S3 → Azure Blob Storage:
- Bucket → Container
- Object/Key → Blob
- presigned URL → SAS Token URL

SDK: azure-storage-blob (SDK oficial da Microsoft)
Documentação: https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python
"""

import io
import mimetypes
import uuid
import time
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from azure.storage.blob import (
    BlobServiceClient,
    BlobClient,
    ContainerClient,
    generate_blob_sas,
    BlobSasPermissions,
    ContentSettings
)
from azure.core.exceptions import AzureError, ResourceNotFoundError
from fastapi import HTTPException

from ..settings import settings

# ============================================================
# CONFIGURAÇÃO
# ============================================================

AZURE_BLOB_CONNECTION_STRING = os.getenv("AZURE_BLOB_CONNECTION_STRING", "")
AZURE_BLOB_ACCOUNT_NAME = os.getenv("AZURE_BLOB_ACCOUNT_NAME", "")
AZURE_BLOB_ACCOUNT_KEY = os.getenv("AZURE_BLOB_ACCOUNT_KEY", "")

# Validação de configuração
if not AZURE_BLOB_CONNECTION_STRING and not (AZURE_BLOB_ACCOUNT_NAME and AZURE_BLOB_ACCOUNT_KEY):
    raise RuntimeError(
        "Configure AZURE_BLOB_CONNECTION_STRING ou (AZURE_BLOB_ACCOUNT_NAME + AZURE_BLOB_ACCOUNT_KEY) no .env"
    )

# Inicializa o cliente
if AZURE_BLOB_CONNECTION_STRING:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
    # Extrai account name da connection string
    for part in AZURE_BLOB_CONNECTION_STRING.split(";"):
        if part.startswith("AccountName="):
            AZURE_BLOB_ACCOUNT_NAME = part.split("=")[1]
            break
else:
    account_url = f"https://{AZURE_BLOB_ACCOUNT_NAME}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(
        account_url=account_url,
        credential=AZURE_BLOB_ACCOUNT_KEY
    )

# Container padrão (equivalente ao BUCKET_RAW do S3)
CONTAINER_RAW = os.getenv("AZURE_BLOB_CONTAINER", settings.S3_BUCKET_RAW if hasattr(settings, 'S3_BUCKET_RAW') else "photo-find-raw")

# Tempo de expiração para URLs assinadas (em segundos)
EXPIRE = getattr(settings, 'PRESIGNED_EXPIRE_SECONDS', 3600)

# Alias para compatibilidade com código existente
BUCKET_RAW = CONTAINER_RAW


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _get_container_client(container: str) -> ContainerClient:
    """Obtém cliente do container, criando se não existir."""
    container_client = blob_service_client.get_container_client(container)
    
    try:
        container_client.get_container_properties()
    except ResourceNotFoundError:
        container_client.create_container()
        print(f"[Azure Blob] Container criado: {container}")
    
    return container_client


def _get_blob_client(container: str, blob_name: str) -> BlobClient:
    """Obtém cliente do blob."""
    return blob_service_client.get_blob_client(container=container, blob=blob_name)


# ============================================================
# UPLOAD DE ARQUIVOS
# ============================================================

def put_bytes(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream"):
    """Faz upload de bytes para o Azure Blob Storage."""
    try:
        blob_client = _get_blob_client(bucket, key)
        content_settings = ContentSettings(content_type=content_type or "application/octet-stream")
        blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
        print(f"[Azure Blob] Upload realizado: {bucket}/{key} ({len(data)} bytes)")
    except AzureError as e:
        print(f"[Azure Blob] Erro ao enviar {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao enviar {key}: {e}")
    except Exception as e:
        print(f"[Azure Blob] Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao enviar arquivo: {e}")


# ============================================================
# DOWNLOAD DE ARQUIVOS
# ============================================================

def get_blob_bytes(bucket: str, key: str) -> bytes:
    """Baixa um blob como bytes. Usada pelo azure_face.py."""
    try:
        blob_client = _get_blob_client(bucket, key)
        download_stream = blob_client.download_blob()
        data = download_stream.readall()
        print(f"[Azure Blob] Download realizado: {bucket}/{key} ({len(data)} bytes)")
        return data
    except ResourceNotFoundError:
        print(f"[Azure Blob] Blob nao encontrado: {bucket}/{key}")
        raise HTTPException(status_code=404, detail=f"Arquivo nao encontrado: {key}")
    except AzureError as e:
        print(f"[Azure Blob] Erro ao baixar {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao baixar {key}: {e}")


# ============================================================
# URLs PRÉ-ASSINADAS (SAS)
# ============================================================

def presign_get(bucket: str, key: str, expires: int = EXPIRE) -> str:
    """Gera URL com SAS token para download (GET)."""
    try:
        expiry_time = datetime.now(timezone.utc) + timedelta(seconds=expires)
        sas_token = generate_blob_sas(
            account_name=AZURE_BLOB_ACCOUNT_NAME,
            container_name=bucket,
            blob_name=key,
            account_key=AZURE_BLOB_ACCOUNT_KEY or _get_account_key_from_connection_string(),
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time
        )
        return f"https://{AZURE_BLOB_ACCOUNT_NAME}.blob.core.windows.net/{bucket}/{key}?{sas_token}"
    except Exception as e:
        print(f"[Azure Blob] Erro ao gerar URL assinada para {key}: {e}")
        return f"https://{AZURE_BLOB_ACCOUNT_NAME}.blob.core.windows.net/{bucket}/{key}"


def presign_put(bucket: str, key: str, content_type: str, expires: int = EXPIRE) -> str:
    """Gera URL com SAS token para upload (PUT)."""
    try:
        expiry_time = datetime.now(timezone.utc) + timedelta(seconds=expires)
        sas_token = generate_blob_sas(
            account_name=AZURE_BLOB_ACCOUNT_NAME,
            container_name=bucket,
            blob_name=key,
            account_key=AZURE_BLOB_ACCOUNT_KEY or _get_account_key_from_connection_string(),
            permission=BlobSasPermissions(write=True, create=True),
            expiry=expiry_time,
            content_type=content_type
        )
        return f"https://{AZURE_BLOB_ACCOUNT_NAME}.blob.core.windows.net/{bucket}/{key}?{sas_token}"
    except Exception as e:
        print(f"[Azure Blob] Erro ao gerar URL de upload para {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar URL de upload: {e}")


def _get_account_key_from_connection_string() -> str:
    """Extrai a account key da connection string."""
    if not AZURE_BLOB_CONNECTION_STRING:
        return ""
    for part in AZURE_BLOB_CONNECTION_STRING.split(";"):
        if part.startswith("AccountKey="):
            return part.split("=", 1)[1]
    return ""


# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def guess_ext(content_type: str) -> str:
    """Adivinha extensão do arquivo pelo content-type."""
    ext = mimetypes.guess_extension(content_type) or ""
    return ".jpg" if ext == ".jpe" else ext


def make_object_key(event_slug: str, original_name: str) -> str:
    """Gera chave única para o objeto."""
    ts = int(time.time())
    return f"{event_slug}/photos/{ts}-{uuid.uuid4().hex}-{original_name}"


# ============================================================
# LISTAGEM DE ARQUIVOS
# ============================================================

def list_keys_in_prefix(bucket: str, prefix: str) -> list[str]:
    """Lista todas as chaves (blobs) com um determinado prefixo."""
    keys = []
    try:
        container_client = _get_container_client(bucket)
        blobs = container_client.list_blobs(name_starts_with=prefix)
        for blob in blobs:
            keys.append(blob.name)
        print(f"[Azure Blob] Listados {len(keys)} blobs com prefixo '{prefix}'")
    except AzureError as e:
        print(f"[Azure Blob] Erro ao listar prefixo {prefix}: {e}")
    return keys


async def list_s3_files(prefix: str, bucket: str = None) -> list[dict]:
    """Lista arquivos com URLs. Mantém nome para compatibilidade."""
    if bucket is None:
        bucket = CONTAINER_RAW
    items = []
    try:
        container_client = _get_container_client(bucket)
        blobs = container_client.list_blobs(name_starts_with=prefix)
        for blob in blobs:
            key = blob.name
            url = f"https://{AZURE_BLOB_ACCOUNT_NAME}.blob.core.windows.net/{bucket}/{key}"
            items.append({"key": key.split('/')[-1], "url": url})
    except AzureError as e:
        print(f"[Azure Blob] Erro ao listar arquivos do prefixo {prefix}: {e}")
    return items


# ============================================================
# DELEÇÃO DE ARQUIVOS
# ============================================================

def delete_object(bucket: str, key: str) -> None:
    """Remove um blob do container."""
    try:
        blob_client = _get_blob_client(bucket, key)
        blob_client.delete_blob()
        print(f"[Azure Blob] Removido: {bucket}/{key}")
    except ResourceNotFoundError:
        print(f"[Azure Blob] Blob ja nao existia: {bucket}/{key}")
    except AzureError as e:
        print(f"[Azure Blob] Falha ao apagar {bucket}/{key}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao apagar arquivo: {e}")
    except Exception as e:
        print(f"[Azure Blob] Erro inesperado ao apagar {bucket}/{key}: {e}")
        raise HTTPException(status_code=500, detail="Erro inesperado ao apagar arquivo")


# ============================================================
# FUNÇÕES DE VERIFICAÇÃO
# ============================================================

def blob_exists(bucket: str, key: str) -> bool:
    """Verifica se um blob existe."""
    try:
        blob_client = _get_blob_client(bucket, key)
        blob_client.get_blob_properties()
        return True
    except ResourceNotFoundError:
        return False
    except:
        return False


def get_blob_info(bucket: str, key: str) -> Optional[dict]:
    """Retorna informações sobre um blob."""
    try:
        blob_client = _get_blob_client(bucket, key)
        props = blob_client.get_blob_properties()
        return {
            "name": props.name,
            "size": props.size,
            "content_type": props.content_settings.content_type,
            "created": props.creation_time.isoformat() if props.creation_time else None,
            "modified": props.last_modified.isoformat() if props.last_modified else None,
        }
    except ResourceNotFoundError:
        return None
    except:
        return None
