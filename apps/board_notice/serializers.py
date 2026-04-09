from rest_framework import serializers

from .models import BoardNotice


def _strip_fields(data: dict) -> dict:
    out = dict(data)
    for key in (
        "title_ko",
        "title_en",
        "subtitle_ko",
        "subtitle_en",
        "content_ko",
        "content_en",
    ):
        if key in out and isinstance(out[key], str):
            out[key] = out[key].strip()
    return out


class BoardNoticeWriteSerializer(serializers.ModelSerializer):
    """관리자 생성·수정 — 한·영 필드 전체."""

    class Meta:
        model = BoardNotice
        fields = (
            "title_ko",
            "title_en",
            "subtitle_ko",
            "subtitle_en",
            "content_ko",
            "content_en",
            "is_pinned",
        )

    def _merged_str(self, attrs: dict, key: str) -> str:
        if key in attrs and attrs[key] is not None:
            return (attrs[key] or "").strip() if isinstance(attrs[key], str) else ""
        if self.instance:
            return (getattr(self.instance, key, "") or "").strip()
        return ""

    def validate(self, attrs):
        tko = self._merged_str(attrs, "title_ko")
        ten = self._merged_str(attrs, "title_en")
        cko = self._merged_str(attrs, "content_ko")
        cen = self._merged_str(attrs, "content_en")
        if not tko and not ten:
            raise serializers.ValidationError(
                {"title_ko": "한글 또는 영문 제목 중 하나는 입력해야 합니다."}
            )
        if not cko and not cen:
            raise serializers.ValidationError(
                {"content_ko": "한글 또는 영문 본문 중 하나는 입력해야 합니다."}
            )
        return attrs

    def create(self, validated_data):
        validated_data = _strip_fields(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = _strip_fields(validated_data)
        return super().update(instance, validated_data)


class BoardNoticeAdminListSerializer(serializers.ModelSerializer):
    """관리자 목록 — 편집용 원본 필드."""

    class Meta:
        model = BoardNotice
        fields = (
            "id",
            "title_ko",
            "title_en",
            "subtitle_ko",
            "subtitle_en",
            "is_pinned",
            "view_count",
            "created_at",
        )


class BoardNoticeAdminDetailSerializer(serializers.ModelSerializer):
    """관리자 상세."""

    class Meta:
        model = BoardNotice
        fields = (
            "id",
            "title_ko",
            "title_en",
            "subtitle_ko",
            "subtitle_en",
            "content_ko",
            "content_en",
            "is_pinned",
            "view_count",
            "created_at",
        )


class BoardNoticePublicListSerializer(serializers.ModelSerializer):
    """공개 목록 — `lang`에 맞춰 title·subtitle만 노출."""

    title = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()

    class Meta:
        model = BoardNotice
        fields = ("id", "title", "subtitle", "is_pinned", "view_count", "created_at")

    def _lang(self) -> str:
        l = self.context.get("lang") or "ko"
        return l if l in ("ko", "en") else "ko"

    def get_title(self, obj: BoardNotice) -> str:
        if self._lang() == "en":
            return (obj.title_en or "").strip()
        return (obj.title_ko or "").strip()

    def get_subtitle(self, obj: BoardNotice) -> str:
        if self._lang() == "en":
            return (obj.subtitle_en or "").strip()
        return (obj.subtitle_ko or "").strip()


class BoardNoticePublicDetailSerializer(BoardNoticePublicListSerializer):
    content = serializers.SerializerMethodField()

    class Meta(BoardNoticePublicListSerializer.Meta):
        fields = ("id", "title", "subtitle", "content", "is_pinned", "view_count", "created_at")

    def get_content(self, obj: BoardNotice) -> str:
        if self._lang() == "en":
            return obj.content_en or ""
        return obj.content_ko or ""
