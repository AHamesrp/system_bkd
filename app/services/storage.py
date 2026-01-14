"""
storage.py - Wrapper para Storage (Azure Blob / AWS S3)

Roteia automaticamente entre Azure e AWS baseado em settings.STORAGE_PROVIDER.
Usa lazy import para evitar falhas se o provider nao estiver configurado.
"""

from app.settings import settings


def _get_impl():
    """Lazy import do modulo correto baseado no provider."""
    provider = getattr(settings, "STORAGE_PROVIDER", "azure")
    if provider == "azure":
        from app.services import azure_blob as impl
        return impl
    if provider == "aws":
        from app.services import s3 as impl
        return impl
    raise RuntimeError(f"STORAGE_PROVIDER invalido: {provider!r}. Use 'azure' ou 'aws'.")


def get_bucket_raw() -> str:
    """Retorna o bucket/container padrao."""
    return _get_impl().BUCKET_RAW


def put_bytes(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream"):
    """Upload de bytes para storage."""
    return _get_impl().put_bytes(bucket, key, data, content_type)


def get_bytes(bucket: str, key: str) -> bytes:
    """Download de bytes do storage."""
    impl = _get_impl()
    provider = getattr(settings, "STORAGE_PROVIDER", "azure")

    if provider == "azure":
        return impl.get_blob_bytes(bucket, key)

    # AWS fallback
    obj = impl.s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read()


def presign_get(bucket: str, key: str, expires: int = None) -> str:
    """Gera URL assinada para download."""
    if expires is None:
        expires = settings.PRESIGNED_EXPIRE_SECONDS
    return _get_impl().presign_get(bucket, key, expires)


def presign_put(bucket: str, key: str, content_type: str, expires: int = None) -> str:
    """Gera URL assinada para upload."""
    if expires is None:
        expires = settings.PRESIGNED_EXPIRE_SECONDS
    return _get_impl().presign_put(bucket, key, content_type, expires)


def make_object_key(event_slug: str, original_name: str) -> str:
    """Gera chave unica para o objeto."""
    return _get_impl().make_object_key(event_slug, original_name)


def list_keys_in_prefix(bucket: str, prefix: str) -> list[str]:
    """Lista chaves com determinado prefixo."""
    return _get_impl().list_keys_in_prefix(bucket, prefix)


async def list_s3_files(prefix: str, bucket: str = None) -> list[dict]:
    """Lista arquivos com URLs."""
    impl = _get_impl()
    if bucket is None:
        bucket = impl.BUCKET_RAW
    return await impl.list_s3_files(prefix, bucket=bucket)


def delete_object(bucket: str, key: str) -> None:
    """Remove objeto do storage."""
    return _get_impl().delete_object(bucket, key)


def guess_ext(content_type: str) -> str:
    """Adivinha extensao pelo content-type."""
    return _get_impl().guess_ext(content_type)
