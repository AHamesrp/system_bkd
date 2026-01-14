import importlib
import boto3
from moto import mock_aws
import pytest

from app.settings import settings
from unittest.mock import patch


@mock_aws
def test_rekognition_basic_flow():
    # Prepare mocked S3
    s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
    s3_client.create_bucket(Bucket=settings.S3_BUCKET_RAW)
    s3_client.put_object(Bucket=settings.S3_BUCKET_RAW, Key="face1.jpg", Body=b"fakejpgdata")

    # Reload rekognition module so it uses moto's mocked AWS
    rek_mod = importlib.reload(importlib.import_module('app.services.rekognition'))

    # Patch the module's client object methods to avoid moto limitations
    with patch.object(rek_mod, 'rk') as fake_rk:
        fake_rk.list_collections.return_value = {'CollectionIds': []}
        fake_rk.create_collection.return_value = {}
        fake_rk.index_faces.return_value = {'FaceRecords': []}
        fake_rk.search_faces_by_image.return_value = {'FaceMatches': []}

        event = "smokeevent"
        collection_id = rek_mod.ensure_collection(event)
        assert collection_id == f"evt-{event}"

        # Indexing should return a dict-like response
        resp = rek_mod.index_s3_object(event, settings.S3_BUCKET_RAW, "face1.jpg", external_image_id="id1")
        assert isinstance(resp, dict)

        # Searching should also return a dict-like response
        search = rek_mod.search_by_image_bytes(event, b"fakejpgdata")
        assert isinstance(search, dict)
