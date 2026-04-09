"""
상품 옵션 이미지 등 — PlanDoc/s3Rules.md: 비공개 버킷이면 Presigned GET, 미설정 시 MEDIA 로컬 저장.
객체 키 접두사: product-option-items/
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

PRODUCT_OPTION_PREFIX = "product-option-items"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


def is_s3_configured() -> bool:
    return bool(getattr(settings, "AWS_S3_BUCKET_NAME", "") or "")


def _normalize_ext(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return ".bin"
    return ext


def generate_product_option_key(original_name: str) -> str:
    now = timezone.now()
    ext = _normalize_ext(original_name)
    return f"{PRODUCT_OPTION_PREFIX}/{now:%Y/%m}/{uuid.uuid4().hex}{ext}"


def upload_product_option_file(uploaded_file) -> str:
    """
    파일을 S3 또는 MEDIA_ROOT 아래 동일 키 경로에 저장하고, DB에 넣을 객체 키 문자열을 반환한다.
    """
    key = generate_product_option_key(getattr(uploaded_file, "name", "upload"))
    content_type = getattr(uploaded_file, "content_type", "") or "application/octet-stream"

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("허용되지 않은 이미지 형식입니다.")

    if is_s3_configured():
        try:
            import boto3  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError("boto3가 필요합니다. requirements.txt를 확인하세요.") from exc

        bucket = settings.AWS_S3_BUCKET_NAME
        region = getattr(settings, "AWS_S3_REGION", "ap-northeast-2")
        client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        extra = {"ContentType": content_type}
        uploaded_file.seek(0)
        client.upload_fileobj(uploaded_file, Bucket=bucket, Key=key, ExtraArgs=extra)
        logger.info("S3 upload ok key=%s", key)
        return key

    root = Path(settings.MEDIA_ROOT)
    dest = root / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    uploaded_file.seek(0)
    with open(dest, "wb") as out:
        for chunk in uploaded_file.chunks():
            out.write(chunk)
    logger.info("Local media upload ok key=%s", key)
    return key


def delete_storage_key(key: str | None) -> None:
    if not key or not key.startswith(PRODUCT_OPTION_PREFIX + "/"):
        return
    if is_s3_configured():
        try:
            import boto3  # noqa: PLC0415
        except ImportError:
            return
        bucket = settings.AWS_S3_BUCKET_NAME
        region = getattr(settings, "AWS_S3_REGION", "ap-northeast-2")
        client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        try:
            client.delete_object(Bucket=bucket, Key=key)
        except Exception:
            logger.exception("S3 delete failed key=%s", key)
        return
    path = Path(settings.MEDIA_ROOT) / key
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        logger.exception("Local delete failed path=%s", path)


def presigned_get_url(key: str) -> str | None:
    if not key or not is_s3_configured():
        return None
    try:
        import boto3  # noqa: PLC0415
    except ImportError:
        return None
    bucket = settings.AWS_S3_BUCKET_NAME
    region = getattr(settings, "AWS_S3_REGION", "ap-northeast-2")
    client = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )
    expires = int(getattr(settings, "AWS_S3_PRESIGNED_GET_EXPIRES", 604800))
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


def image_url_for_key(key: str | None, request) -> str | None:
    """목록·상세 API용 — S3면 Presigned, 로컬이면 MEDIA 절대 URL."""
    if not key:
        return None
    if key.startswith(PRODUCT_OPTION_PREFIX + "/") and is_s3_configured():
        url = presigned_get_url(key)
        if url:
            return url
    if request:
        return request.build_absolute_uri(settings.MEDIA_URL + key.replace("\\", "/"))
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    if not media_url.endswith("/"):
        media_url += "/"
    base = getattr(settings, "SITE_PUBLIC_URL", "").rstrip("/")
    if base:
        return f"{base}{media_url}{key}"
    return f"{media_url}{key}"
