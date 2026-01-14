"""
face.py - Wrapper para Face Recognition (AWS Rekognition)

Roteia para AWS Rekognition baseado em settings.FACE_PROVIDER (aws).
Usa lazy import para evitar falhas se o provider nao estiver configurado.
"""

from app.settings import settings


def _get_impl():
    """Lazy import do modulo correto baseado no provider."""
    provider = getattr(settings, "FACE_PROVIDER", "aws")
    if provider == "aws":
        from app.services import rekognition as impl
        return impl
    raise RuntimeError(f"FACE_PROVIDER invalido: {provider!r}. Use 'aws'.")


def ensure_collection(event_slug: str) -> str:
    """Garante que a collection/facelist do evento exista."""
    return _get_impl().ensure_collection(event_slug)


def index_s3_object(event_slug: str, bucket: str, file_key: str, external_image_id: str = None) -> dict:
    """Indexa faces de uma imagem no storage."""
    return _get_impl().index_s3_object(event_slug, bucket, file_key, external_image_id)


def search_by_image_bytes(event_slug: str, data: bytes, max_faces: int = 50, threshold: int = 75) -> dict:
    """Busca faces similares a partir de bytes da imagem."""
    return _get_impl().search_by_image_bytes(event_slug, data, max_faces, threshold)


def sanitize_key_for_rekognition(s: str) -> str:
    """Sanitiza string para uso como ID."""
    return _get_impl().sanitize_key_for_rekognition(s)


def reindex_all(event_slug: str, bucket: str, keys: list[str]):
    """Reindexa todas as fotos de um evento."""
    return _get_impl().reindex_all(event_slug, bucket, keys)
