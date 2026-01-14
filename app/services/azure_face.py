"""
azure_face.py - Servico de Reconhecimento Facial com Azure Face API
"""

import os
import re
import httpx
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

AZURE_FACE_ENDPOINT = os.getenv("AZURE_FACE_ENDPOINT", "")
AZURE_FACE_KEY = os.getenv("AZURE_FACE_KEY", "")

HEADERS = {
    "Ocp-Apim-Subscription-Key": AZURE_FACE_KEY,
    "Content-Type": "application/json"
}

FACELISTS_CACHE = set()
FACELIST_PREFIX = os.getenv("AZURE_FACELIST_PREFIX", "evt-")

def _get_api_url(path: str) -> str:
    return f"{AZURE_FACE_ENDPOINT.rstrip('/')}/face/v1.0/{path.lstrip('/')}"

def sanitize_key_for_rekognition(s: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.\-]', '_', s)[:128]

def sanitize_key_for_azure(s: str) -> str:
    return sanitize_key_for_rekognition(s)

def ensure_collection(event_slug: str) -> str:
    facelist_id = f"{FACELIST_PREFIX}{sanitize_key_for_azure(event_slug)}"[:64]
    if facelist_id in FACELISTS_CACHE:
        return facelist_id
    with httpx.Client(timeout=30) as client:
        check = client.get(_get_api_url(f"facelists/{facelist_id}"), headers=HEADERS)
        if check.status_code == 200:
            FACELISTS_CACHE.add(facelist_id)
            return facelist_id
        if check.status_code == 404:
            body = {"name": event_slug[:128], "recognitionModel": "recognition_04"}
            create = client.put(_get_api_url(f"facelists/{facelist_id}"), headers=HEADERS, json=body)
            if create.status_code in (200, 201):
                FACELISTS_CACHE.add(facelist_id)
                return facelist_id
            raise RuntimeError(f"Erro ao criar FaceList: {create.text}")
        raise RuntimeError(f"Erro ao verificar FaceList: {check.text}")

def index_image_bytes(event_slug: str, image_data: bytes, external_image_id: str) -> dict:
    facelist_id = ensure_collection(event_slug)
    with httpx.Client(timeout=60) as client:
        detect_headers = {"Ocp-Apim-Subscription-Key": AZURE_FACE_KEY, "Content-Type": "application/octet-stream"}
        detect_params = {"returnFaceId": "true", "recognitionModel": "recognition_04", "detectionModel": "detection_03"}
        detect = client.post(_get_api_url("detect"), headers=detect_headers, params=detect_params, content=image_data)
        if detect.status_code != 200:
            return {"indexed": 0, "error": detect.text}
        faces = detect.json()
        if not faces:
            return {"indexed": 0, "reason": "no_faces_detected"}
        indexed = 0
        for face in faces:
            face_id = face.get("faceId")
            if not face_id:
                continue
            user_data = external_image_id[:1024]
            add_params = {"userData": user_data}
            add_headers = {"Ocp-Apim-Subscription-Key": AZURE_FACE_KEY, "Content-Type": "application/octet-stream"}
            add = client.post(_get_api_url(f"facelists/{facelist_id}/persistedfaces"), headers=add_headers, params=add_params, content=image_data)
            if add.status_code in (200, 201):
                indexed += 1
        return {"indexed": indexed, "faces_detected": len(faces)}

def index_s3_object(event_slug: str, bucket: str, file_key: str, external_image_id: str = None) -> dict:
    from app.services.storage import get_bytes
    image_data = get_bytes(bucket, file_key)
    ext_id = external_image_id or file_key
    return index_image_bytes(event_slug, image_data, ext_id)

def search_by_image_bytes(event_slug: str, data: bytes, max_faces: int = 50, threshold: int = 75) -> dict:
    facelist_id = f"{FACELIST_PREFIX}{sanitize_key_for_azure(event_slug)}"[:64]
    with httpx.Client(timeout=60) as client:
        detect_headers = {"Ocp-Apim-Subscription-Key": AZURE_FACE_KEY, "Content-Type": "application/octet-stream"}
        detect_params = {"returnFaceId": "true", "recognitionModel": "recognition_04", "detectionModel": "detection_03"}
        detect = client.post(_get_api_url("detect"), headers=detect_headers, params=detect_params, content=data)
        if detect.status_code != 200:
            return {"FaceMatches": [], "error": detect.text}
        faces = detect.json()
        if not faces:
            return {"FaceMatches": []}
        face_id = faces[0].get("faceId")
        if not face_id:
            return {"FaceMatches": []}
        find_body = {"faceId": face_id, "faceListId": facelist_id, "maxNumOfCandidatesReturned": max_faces}
        find = client.post(_get_api_url("findsimilars"), headers=HEADERS, json=find_body)
        if find.status_code != 200:
            return {"FaceMatches": [], "error": find.text}
        similar = find.json()
        matches = []
        for s in similar:
            conf = s.get("confidence", 0) * 100
            if conf >= threshold:
                matches.append({
                    "Similarity": conf,
                    "Face": {"FaceId": s.get("persistedFaceId", ""), "ExternalImageId": s.get("userData", "")}
                })
        return {"FaceMatches": matches}

def reindex_all(event_slug: str, bucket: str, keys: list[str]):
    def _index(key):
        try:
            return index_s3_object(event_slug, bucket, key)
        except Exception as e:
            return {"error": str(e), "key": key}
    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(_index, keys))
