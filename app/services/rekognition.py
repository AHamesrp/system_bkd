import boto3
import os
import re
from concurrent.futures import ThreadPoolExecutor

rk = boto3.client(
    "rekognition",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)
COLLECTIONS_CACHE = set()


def ensure_collection(event_slug: str) -> str:
    """
    Garante que a collection do evento exista no Rekognition.
    Se não existir, cria automaticamente.
    """
    collection_id = f"evt-{event_slug}"

    # Se já estiver no cache, não tenta criar novamente
    if collection_id in COLLECTIONS_CACHE:
        return collection_id

    try:
        # Verifica se a collection já existe na AWS
        existing_collections = rk.list_collections(MaxResults=100)["CollectionIds"]
        if collection_id not in existing_collections:
            rk.create_collection(CollectionId=collection_id)
            print(f"[Rekognition] Collection criada: {collection_id}")
    except Exception as e:
        print(f"[Rekognition] Erro ao garantir collection '{collection_id}': {e}")

    COLLECTIONS_CACHE.add(collection_id)
    return collection_id


def sanitize_key_for_rekognition(s: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.:-]", "_", s)
    return safe[:100]


def index_s3_object(event_slug: str, bucket: str, file_key: str, external_image_id: str):
    """
    Indexa uma face no Rekognition usando um ExternalImageId explícito.
    Se a collection não existir, ela será criada automaticamente.
    """
    collection_id = ensure_collection(event_slug)

    try:
        return rk.index_faces(
            CollectionId=collection_id,
            Image={"S3Object": {"Bucket": bucket, "Name": file_key}},
            ExternalImageId=external_image_id,
            DetectionAttributes=[],
            MaxFaces=80,
            QualityFilter="AUTO",
        )
    except rk.exceptions.ResourceNotFoundException:
        # Se ainda assim não existir, cria e tenta de novo
        rk.create_collection(CollectionId=collection_id)
        print(f"[Rekognition] Collection criada sob demanda: {collection_id}")
        return rk.index_faces(
            CollectionId=collection_id,
            Image={"S3Object": {"Bucket": bucket, "Name": file_key}},
            ExternalImageId=external_image_id,
            DetectionAttributes=[],
            MaxFaces=80,
            QualityFilter="AUTO",
        )


def search_by_image_bytes(event_slug: str, data: bytes, max_faces: int = 50, threshold: int = 75):
    """
    Busca faces por imagem, garantindo que a collection exista.
    """
    collection_id = ensure_collection(event_slug)
    try:
        return rk.search_faces_by_image(
            CollectionId=collection_id,
            Image={"Bytes": data},
            MaxFaces=max_faces,
            FaceMatchThreshold=threshold,
        )
    except rk.exceptions.ResourceNotFoundException:
        rk.create_collection(CollectionId=collection_id)
        print(f"[Rekognition] Collection criada sob demanda para busca: {collection_id}")
        return rk.search_faces_by_image(
            CollectionId=collection_id,
            Image={"Bytes": data},
            MaxFaces=max_faces,
            FaceMatchThreshold=threshold,
        )


def reindex_all(event_slug: str, bucket: str, keys: list[str]):
    """
    Reindexa todas as fotos de um evento, garantindo a consistência do ID.
    Cria a collection caso não exista.
    """
    ensure_collection(event_slug)

    def _index(key):
        try:
            image_id = key.split("/")[-1]
            index_s3_object(event_slug, bucket, key, image_id)
            print(f"[Reindexação] Reindexado com sucesso: {key}")
        except Exception as e:
            print(f"[Reindexação] Erro ao reindexar {key}: {e}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(_index, keys)
