"""공지 한·영 필드 가용성 (목록·상세 필터)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import BoardNotice


def notice_has_lang(notice: "BoardNotice", lang: str) -> bool:
    """해당 언어로 표시할 텍스트가 하나라도 있으면 True."""
    if lang == "en":
        return bool(
            (notice.title_en or "").strip()
            or (notice.subtitle_en or "").strip()
            or (notice.content_en or "").strip()
        )
    return bool(
        (notice.title_ko or "").strip()
        or (notice.subtitle_ko or "").strip()
        or (notice.content_ko or "").strip()
    )
