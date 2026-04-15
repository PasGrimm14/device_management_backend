from minio import Minio

from app.core.config import settings


def get_minio_client() -> Minio:
    """Interner Client für Upload/Bucket-Operationen (App → MinIO)."""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )


def get_minio_public_client() -> Minio:
    """Client für Presigned-URLs – nutzt die öffentlich erreichbare Adresse."""
    return Minio(
        settings.MINIO_PUBLIC_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=True,
    )


def ensure_bucket_exists(client: Minio) -> None:
    """Erstellt den Bucket falls er noch nicht existiert."""
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)
