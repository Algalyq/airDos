import io
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

settings = get_settings()


def get_minio_client(external: bool = False) -> Minio:
    endpoint = settings.MINIO_ENDPOINT
    secure = settings.MINIO_SECURE
    if external and settings.MINIO_EXTERNAL_ENDPOINT:
        endpoint = settings.MINIO_EXTERNAL_ENDPOINT
        if settings.MINIO_EXTERNAL_SECURE is not None:
            secure = settings.MINIO_EXTERNAL_SECURE
    return Minio(
        endpoint,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=secure,
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

    external_client = get_minio_client(external=True)
    return external_client.presigned_get_object(
        bucket,
        storage_key,
        expires=timedelta(seconds=expiry_seconds),
    )
