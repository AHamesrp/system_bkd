import importlib
import boto3
from moto import mock_aws
import pytest

from app.settings import settings


@mock_aws
def test_put_get_list_delete_s3():
    # Prepare mocked S3
    s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
    s3_client.create_bucket(Bucket=settings.S3_BUCKET_RAW)

    # Reload module so it uses moto's mocked AWS
    s3_mod = importlib.reload(importlib.import_module('app.services.s3'))

    key = "smoke/test.txt"

    # Upload
    s3_mod.put_bytes(settings.S3_BUCKET_RAW, key, b"hello-world", content_type="text/plain")

    # Verify object exists and content matches
    obj = s3_client.get_object(Bucket=settings.S3_BUCKET_RAW, Key=key)
    assert obj["Body"].read() == b"hello-world"

    # Presigned URLs
    url_get = s3_mod.presign_get(settings.S3_BUCKET_RAW, key)
    assert url_get.startswith("https://")

    url_put = s3_mod.presign_put(settings.S3_BUCKET_RAW, key, "text/plain")
    assert url_put.startswith("https://")

    # List keys
    keys = s3_mod.list_keys_in_prefix(settings.S3_BUCKET_RAW, "smoke/")
    assert any(k.endswith("test.txt") for k in keys)

    # Delete
    s3_mod.delete_object(settings.S3_BUCKET_RAW, key)
    # After deletion, list should not include the key
    keys_after = s3_mod.list_keys_in_prefix(settings.S3_BUCKET_RAW, "smoke/")
    assert all(not k.endswith("test.txt") for k in keys_after)
