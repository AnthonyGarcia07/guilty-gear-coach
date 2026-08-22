import pytest
from botocore.exceptions import ClientError

from app.core.config import Settings
from app.services.storage import S3CompatibleStorageService, StorageConfigurationError


class FakeS3Client:
    def __init__(self, head_response: dict | None = None, head_error: ClientError | None = None) -> None:
        self.presigned_calls: list[dict] = []
        self.head_calls: list[dict] = []
        self.head_response = head_response or {
            "ContentLength": 123,
            "ContentType": "video/mp4",
            "ETag": '"etag-value"',
            "Metadata": {"replay": "test"},
        }
        self.head_error = head_error

    def generate_presigned_url(self, ClientMethod: str, Params: dict, ExpiresIn: int) -> str:
        self.presigned_calls.append({"ClientMethod": ClientMethod, "Params": Params, "ExpiresIn": ExpiresIn})
        return f"https://storage.example/{Params['Key']}?method={ClientMethod}"

    def head_object(self, Bucket: str, Key: str) -> dict:
        self.head_calls.append({"Bucket": Bucket, "Key": Key})
        if self.head_error:
            raise self.head_error
        return self.head_response


def make_service(client: FakeS3Client | None = None) -> S3CompatibleStorageService:
    return S3CompatibleStorageService(
        endpoint_url="https://account.r2.cloudflarestorage.com",
        bucket_name="ggc-replays",
        region="auto",
        access_key_id="test-access-key",
        secret_access_key="test-secret-key",
        presigned_upload_expiration_seconds=900,
        presigned_download_expiration_seconds=300,
        client=client or FakeS3Client(),
    )


def client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "not found"}}, "HeadObject")


def test_generates_presigned_upload_url_with_private_bucket_target():
    fake_client = FakeS3Client()
    service = make_service(fake_client)

    url = service.generate_presigned_upload_url("users/1/matches/2/replays/3.mp4")

    assert url == "https://storage.example/users/1/matches/2/replays/3.mp4?method=put_object"
    assert fake_client.presigned_calls == [
        {
            "ClientMethod": "put_object",
            "Params": {
                "Bucket": "ggc-replays",
                "Key": "users/1/matches/2/replays/3.mp4",
                "ContentType": "video/mp4",
            },
            "ExpiresIn": 900,
        }
    ]


def test_generates_presigned_download_url():
    fake_client = FakeS3Client()
    service = make_service(fake_client)

    url = service.generate_presigned_download_url("users/1/matches/2/replays/3.mp4")

    assert url == "https://storage.example/users/1/matches/2/replays/3.mp4?method=get_object"
    assert fake_client.presigned_calls == [
        {
            "ClientMethod": "get_object",
            "Params": {
                "Bucket": "ggc-replays",
                "Key": "users/1/matches/2/replays/3.mp4",
            },
            "ExpiresIn": 300,
        }
    ]


def test_reads_object_metadata_with_head_object():
    fake_client = FakeS3Client()
    service = make_service(fake_client)

    metadata = service.get_object_metadata("users/1/matches/2/replays/3.mp4")

    assert metadata is not None
    assert metadata.content_length == 123
    assert metadata.content_type == "video/mp4"
    assert metadata.etag == '"etag-value"'
    assert metadata.metadata == {"replay": "test"}
    assert fake_client.head_calls == [{"Bucket": "ggc-replays", "Key": "users/1/matches/2/replays/3.mp4"}]
    assert service.object_exists("users/1/matches/2/replays/3.mp4") is True


@pytest.mark.parametrize("code", ["404", "NoSuchKey", "NotFound"])
def test_missing_object_metadata_returns_none(code: str):
    service = make_service(FakeS3Client(head_error=client_error(code)))

    assert service.get_object_metadata("users/1/matches/2/replays/missing.mp4") is None
    assert service.object_exists("users/1/matches/2/replays/missing.mp4") is False


def test_unexpected_head_errors_are_not_hidden():
    service = make_service(FakeS3Client(head_error=client_error("AccessDenied")))

    with pytest.raises(ClientError):
        service.get_object_metadata("users/1/matches/2/replays/private.mp4")


def test_rejects_blank_storage_keys():
    service = make_service()

    with pytest.raises(ValueError, match="Storage key is required"):
        service.generate_presigned_upload_url(" ")


def test_builds_from_settings_without_network_when_client_is_injected():
    fake_client = FakeS3Client()
    settings = Settings(
        s3_endpoint_url="https://account.r2.cloudflarestorage.com",
        s3_bucket_name="ggc-replays",
        s3_region="auto",
        s3_access_key_id="access",
        s3_secret_access_key="secret",
    )

    service = S3CompatibleStorageService.from_settings(settings, client=fake_client)

    assert service.bucket_name == "ggc-replays"
    assert service.presigned_upload_expiration_seconds == 900
    assert service.presigned_download_expiration_seconds == 300


def test_missing_storage_configuration_is_rejected():
    settings = Settings(
        s3_endpoint_url=None,
        s3_bucket_name="ggc-replays",
        s3_access_key_id="access",
        s3_secret_access_key="secret",
    )

    with pytest.raises(StorageConfigurationError, match="S3_ENDPOINT_URL must be configured"):
        S3CompatibleStorageService.from_settings(settings, client=FakeS3Client())
