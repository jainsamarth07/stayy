"""S3-compatible file upload service."""

import json
import uuid

import boto3
from botocore.exceptions import ClientError

from app.config import settings


def get_s3_client():
    """Create an S3 client configured for the current environment."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
    )


def _ensure_bucket_exists(s3) -> None:
    """Create the S3 bucket if it does not already exist and ensure it has a public-read policy."""
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except ClientError:
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)

    # Apply a public-read bucket policy so browser <img> tags can load images directly.
    # MinIO buckets default to private — without this every GET returns 403.
    public_read_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{settings.S3_BUCKET_NAME}/*"],
            }
        ],
    })
    try:
        s3.put_bucket_policy(Bucket=settings.S3_BUCKET_NAME, Policy=public_read_policy)
    except ClientError:
        pass  # Policy already set or not supported — images served via signed URLs if needed


def upload_image(file_bytes: bytes, content_type: str, folder: str = "properties") -> str:
    """Upload an image to S3 and return its URL.

    Args:
        file_bytes: Raw image bytes.
        content_type: MIME type (e.g., 'image/jpeg').
        folder: S3 key prefix.

    Returns:
        The public URL of the uploaded image.
    """
    s3 = get_s3_client()
    _ensure_bucket_exists(s3)
    file_ext = content_type.split("/")[-1]
    key = f"{folder}/{uuid.uuid4()}.{file_ext}"

    s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )

    # Use public URL for browser access (S3_ENDPOINT_URL may be internal like http://minio:9000)
    public_base = getattr(settings, "S3_PUBLIC_URL", "") or settings.S3_ENDPOINT_URL
    return f"{public_base}/{settings.S3_BUCKET_NAME}/{key}"


def delete_image(image_url: str) -> bool:
    """Delete an image from S3 by its full URL."""
    s3 = get_s3_client()
    key = image_url.split(f"{settings.S3_BUCKET_NAME}/")[-1]
    try:
        s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        return True
    except ClientError:
        return False
