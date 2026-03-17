"""
S3/R2 storage for PDF statements.
"""

import os
import uuid
from typing import Optional

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def _get_s3_client():
    """Get S3 client configured for standard S3 or Cloudflare R2."""
    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def _get_bucket() -> str:
    return os.getenv("S3_BUCKET", "wealthlens-statements")


async def upload_pdf(pdf_bytes: bytes, user_id: str, filename: str = "") -> Optional[str]:
    """
    Upload a PDF to S3/R2.
    Returns the S3 key or None on failure.
    """
    if not HAS_BOTO3:
        print("Warning: boto3 not installed. PDF storage disabled.")
        return None

    try:
        s3 = _get_s3_client()
        ext = ".pdf"
        key = f"statements/{user_id}/{uuid.uuid4().hex}{ext}"

        s3.put_object(
            Bucket=_get_bucket(),
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            Metadata={"original_filename": filename or "statement.pdf"},
        )

        return key

    except Exception as e:
        print(f"S3 upload error: {e}")
        return None


async def get_pdf_url(key: str, expires_in: int = 3600) -> Optional[str]:
    """
    Get a pre-signed URL for a stored PDF.
    """
    if not HAS_BOTO3:
        return None

    try:
        s3 = _get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": _get_bucket(), "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    except Exception as e:
        print(f"S3 presign error: {e}")
        return None
