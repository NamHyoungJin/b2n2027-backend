"""
상품 옵션·스폰서 등 관리형 키 — PlanDoc/s3Rules.md:
- S3 + AWS_S3_PUBLIC_GET_FOR_MANAGED: 공개 HTTPS URL(버킷에서 GetObject 허용 필요).
- AWS_S3_FORCE_PRESIGNED_FOR_MANAGED: 공개 모드여도 Presigned만(공개 URL 403 대비).
- S3 + 그 외: Presigned GET.
- 버킷 미설정: 로컬 MEDIA.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

PRODUCT_OPTION_PREFIX = "product-option-items"
SPONSOR_PREFIX = "sponsors"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


def is_s3_configured() -> bool:
    return bool(getattr(settings, "AWS_S3_BUCKET_NAME", "") or "")


def _s3_put_extra_args(content_type: str) -> dict:
    extra: dict = {"ContentType": content_type}
    if getattr(settings, "AWS_S3_UPLOAD_ACL_PUBLIC_READ", False):
        extra["ACL"] = "public-read"
    return extra


def public_http_url_for_s3_key(key: str) -> str:
    """가상 호스트 스타일 공개 URL — 버킷 정책(또는 public-read ACL)으로 익명 GetObject 허용 시 img 태그로 표시 가능."""
    bucket = settings.AWS_S3_BUCKET_NAME
    region = getattr(settings, "AWS_S3_REGION", "ap-northeast-2")
    normalized = key.replace("\\", "/").lstrip("/")
    parts = [quote(p, safe="") for p in normalized.split("/") if p != ""]
    path = "/".join(parts)
    return f"https://{bucket}.s3.{region}.amazonaws.com/{path}"


def _normalize_ext(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return ".bin"
    return ext


def generate_product_option_key(original_name: str) -> str:
    now = timezone.now()
    ext = _normalize_ext(original_name)
    return f"{PRODUCT_OPTION_PREFIX}/{now:%Y/%m}/{uuid.uuid4().hex}{ext}"


def generate_sponsor_key(original_name: str) -> str:
    now = timezone.now()
    ext = _normalize_ext(original_name)
    return f"{SPONSOR_PREFIX}/{now:%Y/%m}/{uuid.uuid4().hex}{ext}"


def _upload_fileobj_to_s3(client, bucket: str, key: str, uploaded_file, content_type: str) -> None:
    """ACL public-read 가 버킷에서 거절되면 Content-Type 만으로 재시도."""
    from botocore.exceptions import ClientError  # noqa: PLC0415

    extra = _s3_put_extra_args(content_type)
    uploaded_file.seek(0)
    try:
        client.upload_fileobj(uploaded_file, Bucket=bucket, Key=key, ExtraArgs=extra)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code == "AccessControlListNotSupported" and extra.get("ACL"):
            uploaded_file.seek(0)
            client.upload_fileobj(
                uploaded_file,
                Bucket=bucket,
                Key=key,
                ExtraArgs={"ContentType": content_type},
            )
            logger.warning(
                "S3 ACL public-read not supported; uploaded without ACL — add bucket policy for public GetObject."
            )
        else:
            raise


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
        _upload_fileobj_to_s3(client, bucket, key, uploaded_file, content_type)
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


def upload_sponsor_file(uploaded_file) -> str:
    key = generate_sponsor_key(getattr(uploaded_file, "name", "upload"))
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
        _upload_fileobj_to_s3(client, bucket, key, uploaded_file, content_type)
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
    if not key or not (
        key.startswith(PRODUCT_OPTION_PREFIX + "/") or key.startswith(SPONSOR_PREFIX + "/")
    ):
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


def _local_media_file_exists(key: str) -> bool:
    """MEDIA_ROOT 기준 객체 파일 존재 여부 (로컬 저장 업로드용)."""
    if not key or ".." in key:
        return False
    path = Path(settings.MEDIA_ROOT) / key.replace("\\", "/")
    try:
        return path.is_file()
    except OSError:
        return False


def _absolute_media_url(normalized: str, request) -> str:
    """로컬 MEDIA 절대 URL — 레거시·비관리형 키 또는 S3 미설정 개발용."""
    rel = settings.MEDIA_URL + normalized
    if request:
        return request.build_absolute_uri(rel)
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    if not media_url.endswith("/"):
        media_url += "/"
    base = getattr(settings, "SITE_PUBLIC_URL", "").strip().rstrip("/")
    if base:
        return f"{base}{media_url}{normalized}"
    fallback = os.getenv("DJANGO_PUBLIC_ORIGIN", "http://localhost:8000").strip().rstrip("/")
    return f"{fallback}{media_url}{normalized}"


def image_url_for_key(key: str | None, request) -> str | None:
    """목록·상세 API용 — 관리형 키는 S3 Presigned만(운영). 로컬 개발만 MEDIA 절대 URL."""
    if not key:
        return None
    normalized = key.replace("\\", "/").lstrip("/")
    is_managed = normalized.startswith(PRODUCT_OPTION_PREFIX + "/") or normalized.startswith(
        SPONSOR_PREFIX + "/"
    )

    # 상품 옵션·스폰서: 공개 읽기 URL(버킷 정책/ACL) 또는 Presigned
    if is_managed and is_s3_configured():
        use_public = getattr(settings, "AWS_S3_PUBLIC_GET_FOR_MANAGED", False) and not getattr(
            settings, "AWS_S3_FORCE_PRESIGNED_FOR_MANAGED", False
        )
        if use_public:
            return public_http_url_for_s3_key(normalized)
        url = presigned_get_url(normalized)
        if not url:
            logger.warning("S3 presigned GET unavailable for key=%s (credentials·객체 존재 확인)", normalized)
        return url

    # 관리형 키 + S3 미설정: 로컬 개발만 MEDIA
    if is_managed and not is_s3_configured():
        if not _local_media_file_exists(normalized):
            logger.warning(
                "S3 미설정·로컬 파일 없음 key=%s (MEDIA_ROOT=%s)",
                normalized,
                settings.MEDIA_ROOT,
            )
        return _absolute_media_url(normalized, request)

    # 레거시 ImageField 등 비관리형 경로
    return _absolute_media_url(normalized, request)
