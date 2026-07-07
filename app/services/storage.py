import io
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

settings = get_settings()


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE,
        region=settings.MINIO_REGION,
    )


def ensure_bucket_exists(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def upload_file(
    file_data: bytes,
    content_type: str,
    user_id: uuid.UUID,
    extension: str,
    bucket: str = settings.MINIO_BUCKET,
) -> str:
    client = get_minio_client()
    ensure_bucket_exists(client, bucket)

    file_id = uuid.uuid4()
    key = f"user_{user_id}/documents/{file_id}.{extension.lstrip('.')}"

    client.put_object(
        bucket,
        key,
        io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )

    return key


def get_presigned_url(
    storage_key: str,
    bucket: str = settings.MINIO_BUCKET,
    expiry_seconds: int = 900,
) -> str:
    client = get_minio_client()
    ensure_bucket_exists(client, bucket)

    return client.presigned_get_object(
        bucket,
        storage_key,
        expires=timedelta(seconds=expiry_seconds),
    )
