from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Protocol


class MediaStorageProvider(Protocol):
    def save(self, relative_path: str, source_path: str) -> str:
        """Copy/upload file to storage. Returns the stored relative_path."""
        ...

    def get_url(self, relative_path: str) -> str:
        """Return a URL (or local path) for serving the file."""
        ...

    def delete(self, relative_path: str) -> None:
        """Delete the file from storage."""
        ...


class LocalMediaStorageProvider:
    """Stores files under MEDIA_ROOT. Default for local dev."""

    def __init__(self, media_root: str | None = None) -> None:
        from django.conf import settings

        self._root = Path(media_root or settings.MEDIA_ROOT)

    def save(self, relative_path: str, source_path: str) -> str:
        dest = self._root / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest)
        return relative_path

    def get_url(self, relative_path: str) -> str:
        from django.conf import settings

        return f"{settings.MEDIA_URL}{relative_path}"

    def delete(self, relative_path: str) -> None:
        target = self._root / relative_path
        if target.exists():
            target.unlink()


class S3MediaStorageProvider:
    """S3-compatible storage via boto3. Activated via MEDIA_STORAGE_PROVIDER=s3."""

    def __init__(self) -> None:
        import boto3  # type: ignore[import-untyped]

        self._bucket = os.environ["S3_BUCKET"]
        endpoint = os.getenv("S3_ENDPOINT_URL")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "auto"),
        )
        self._public_url_base = os.getenv("S3_PUBLIC_URL_BASE", "").rstrip("/")

    def save(self, relative_path: str, source_path: str) -> str:
        self._client.upload_file(source_path, self._bucket, relative_path)
        return relative_path

    def get_url(self, relative_path: str) -> str:
        if self._public_url_base:
            return f"{self._public_url_base}/{relative_path}"
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": relative_path},
            ExpiresIn=3600,
        )

    def delete(self, relative_path: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=relative_path)


def get_storage_provider() -> MediaStorageProvider:
    from django.conf import settings

    provider = getattr(settings, "MEDIA_STORAGE_PROVIDER", "local")
    if provider == "s3":
        return S3MediaStorageProvider()
    return LocalMediaStorageProvider()
