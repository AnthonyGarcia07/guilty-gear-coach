"""Provide a small, backend-only interface to private Cloudflare R2 storage.

Cloudflare R2 supports the same API style as Amazon S3, so boto3 can communicate
with it. Long-lived storage credentials remain on the backend. When the browser
needs to upload or download one file, the backend creates a short-lived
presigned URL that permits only that specific operation.

Keeping boto3 details in this service makes routes easier to read and lets tests
replace real cloud storage with a small fake object.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import Settings


class StorageConfigurationError(RuntimeError):
    pass


class S3Client(Protocol):
    """Describe only the S3 client methods this service needs.

    A ``Protocol`` is similar to an interface: any real or fake object with
    these methods can be passed to the service. Tests therefore do not need R2
    credentials or network access.
    """

    def generate_presigned_url(self, ClientMethod: str, Params: dict[str, Any], ExpiresIn: int) -> str:
        ...

    def head_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        ...

    def delete_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        ...

    def download_file(self, Bucket: str, Key: str, Filename: str) -> None:
        ...


@dataclass(frozen=True)
class StorageObjectMetadata:
    """Hold the file details returned by R2's ``head_object`` operation."""

    content_length: int | None
    content_type: str | None
    etag: str | None
    metadata: dict[str, str]


class S3CompatibleStorageService:
    """Validate storage settings and perform the app's allowed R2 operations."""

    def __init__(
        self,
        *,
        endpoint_url: str,
        bucket_name: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        presigned_upload_expiration_seconds: int,
        presigned_download_expiration_seconds: int,
        client: S3Client | None = None,
    ) -> None:
        self.endpoint_url = require_config_value(endpoint_url, "S3_ENDPOINT_URL")
        self.bucket_name = require_config_value(bucket_name, "S3_BUCKET_NAME")
        self.region = require_config_value(region, "S3_REGION")
        self.presigned_upload_expiration_seconds = require_positive_expiration(
            presigned_upload_expiration_seconds,
            "S3_PRESIGNED_UPLOAD_EXPIRATION_SECONDS",
        )
        self.presigned_download_expiration_seconds = require_positive_expiration(
            presigned_download_expiration_seconds,
            "S3_PRESIGNED_DOWNLOAD_EXPIRATION_SECONDS",
        )
        self._client = client or boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            aws_access_key_id=require_config_value(access_key_id, "S3_ACCESS_KEY_ID"),
            aws_secret_access_key=require_config_value(secret_access_key, "S3_SECRET_ACCESS_KEY"),
            config=Config(signature_version="s3v4"),
        )

    @classmethod
    def from_settings(cls, settings: Settings, client: S3Client | None = None) -> "S3CompatibleStorageService":
        return cls(
            endpoint_url=settings.s3_endpoint_url or "",
            bucket_name=settings.s3_bucket_name or "",
            region=settings.s3_region,
            access_key_id=settings.s3_access_key_id or "",
            secret_access_key=settings.s3_secret_access_key or "",
            presigned_upload_expiration_seconds=settings.s3_presigned_upload_expiration_seconds,
            presigned_download_expiration_seconds=settings.s3_presigned_download_expiration_seconds,
            client=client,
        )

    def generate_presigned_upload_url(self, storage_key: str, *, content_type: str = "video/mp4") -> str:
        # The content type becomes part of the signed request. If the browser
        # sends a different Content-Type header, R2 will reject the upload.
        return self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": require_storage_key(storage_key),
                "ContentType": require_config_value(content_type, "content_type"),
            },
            ExpiresIn=self.presigned_upload_expiration_seconds,
        )

    def generate_presigned_download_url(self, storage_key: str) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": require_storage_key(storage_key),
            },
            ExpiresIn=self.presigned_download_expiration_seconds,
        )

    def get_object_metadata(self, storage_key: str) -> StorageObjectMetadata | None:
        # A pending upload may not have created its R2 object yet. Return None for
        # that expected case, but let connection and permission errors bubble up
        # so the route can report a real storage failure.
        try:
            response = self._client.head_object(Bucket=self.bucket_name, Key=require_storage_key(storage_key))
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise

        return StorageObjectMetadata(
            content_length=response.get("ContentLength"),
            content_type=response.get("ContentType"),
            etag=response.get("ETag"),
            metadata=response.get("Metadata") or {},
        )

    def object_exists(self, storage_key: str) -> bool:
        return self.get_object_metadata(storage_key) is not None

    def delete_object(self, storage_key: str) -> None:
        self._client.delete_object(Bucket=self.bucket_name, Key=require_storage_key(storage_key))

    def download_object_to_file(self, storage_key: str, destination: str | Path) -> None:
        self._client.download_file(self.bucket_name, require_storage_key(storage_key), str(destination))


def require_config_value(value: str, name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise StorageConfigurationError(f"{name} must be configured.")
    return cleaned


def require_positive_expiration(value: int, name: str) -> int:
    if value <= 0:
        raise StorageConfigurationError(f"{name} must be greater than 0.")
    return value


def require_storage_key(storage_key: str) -> str:
    cleaned = storage_key.strip()
    if not cleaned:
        raise ValueError("Storage key is required.")
    return cleaned


"""I created a storage service that uses boto3 to communicate with Cloudflare R2 through its S3-compatible API.

The backend keeps the storage credentials private and generates short-lived presigned URLs so the browser can upload and download videos directly.
I also isolated storage operations behind a service interface so I can test the application using fake storage clients without connecting to R2.
"""
