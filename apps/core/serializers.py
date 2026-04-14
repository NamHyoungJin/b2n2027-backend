from rest_framework import serializers

from apps.core.s3_storage import image_url_for_key

from .models import Inquiry
from .models import Sponsor


MAX_LOGO_BYTES = 5 * 1024 * 1024  # 5MB


class SponsorInquirySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, trim_whitespace=True)
    email = serializers.EmailField()
    company_name = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default='', trim_whitespace=True
    )
    phone = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default='', trim_whitespace=True
    )
    message = serializers.CharField(
        max_length=5000, required=False, allow_blank=True, default='', trim_whitespace=True
    )
    logo = serializers.ImageField(required=False, allow_null=True)

    def validate_logo(self, value):
        if value is None:
            return value
        if value.size > MAX_LOGO_BYTES:
            raise serializers.ValidationError('로고 이미지는 5MB 이하만 첨부할 수 있습니다.')
        return value


class GeneralInquirySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, trim_whitespace=True)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200, trim_whitespace=True)
    phone = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default='', trim_whitespace=True
    )
    message = serializers.CharField(
        max_length=5000, required=False, allow_blank=True, default='', trim_whitespace=True
    )


class InquiryListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "type",
            "type_display",
            "status",
            "status_display",
            "name",
            "email",
            "subject",
            "company_name",
            "phone",
            "created_at",
            "answered_at",
        ]


class InquiryDetailSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    answered_by_name = serializers.CharField(source="answered_by.memberShipName", read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "type",
            "type_display",
            "status",
            "status_display",
            "name",
            "email",
            "subject",
            "message",
            "company_name",
            "phone",
            "logo_url",
            "answer",
            "answered_at",
            "answered_by_name",
            "created_at",
            "updated_at",
        ]

    def get_logo_url(self, obj: Inquiry):
        if not obj.logo:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.logo.url
        return request.build_absolute_uri(obj.logo.url)


class InquiryAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(max_length=10000, trim_whitespace=True)


class SponsorAdminSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Sponsor
        fields = [
            "id",
            "name",
            "image_s3_key",
            "image_url",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        """multipart 등록 시 image_s3_key 누락 방지. 수정 시 빈 문자열로 기존 키가 지워지지 않게 함."""
        if self.instance is None:
            key = (attrs.get("image_s3_key") or "").strip()
            if not key:
                raise serializers.ValidationError(
                    {"image_s3_key": "스폰서 이미지를 업로드한 뒤 저장해 주세요."}
                )
        elif "image_s3_key" in attrs and not (attrs.get("image_s3_key") or "").strip():
            attrs.pop("image_s3_key", None)
        return attrs

    def get_image_url(self, obj: Sponsor):
        if obj.image_s3_key:
            return image_url_for_key(obj.image_s3_key, self.context.get("request"))
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class SponsorPublicSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Sponsor
        fields = [
            "id",
            "name",
            "image_url",
            "sort_order",
        ]

    def get_image_url(self, obj: Sponsor):
        if obj.image_s3_key:
            return image_url_for_key(obj.image_s3_key, self.context.get("request"))
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
