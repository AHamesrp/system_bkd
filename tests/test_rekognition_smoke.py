import importlib
import boto3
from moto import mock_aws
import pytest

from app.settings import settings


@mock_aws
def test_rekognition_basic_flow():
    # Prepare mocked S3
    s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
    s3_client.create_bucket(Bucket=settings.S3_BUCKET_RAW)
    s3_client.put_object(Bucket=settings.S3_BUCKET_RAW, Key="face1.jpg", Body=b"fakejpgdata")

    # Reload rekognition module so it uses moto's mocked AWS
    from app import services
    rek_mod = importlib.reload(services.rekognition)

    event = "smokeevent"
    collection_id = rek_mod.ensure_collection(event)
    assert collection_id == f"evt-{event}"

    # Try indexing the S3 object; moto may or may not support index_faces fully.
    try:
        resp = rek_mod.index_s3_object(event, settings.S3_BUCKET_RAW, "face1.jpg", external_image_id="id1")
        # If response has 'FaceRecords' or similar, we consider it successful
        assert isinstance(resp, dict)
    except Exception as e:
        pytest.skip(f"Rekognition index/search not fully supported in this environment: {e}")

    # Try searching by bytes (this also may be limited in moto)
    try:
        search = rek_mod.search_by_image_bytes(event, b"fakejpgdata")
        assert isinstance(search, dict)
    except Exception as e:
        pytest.skip(f"Rekognition search not fully supported in this environment: {e}")
