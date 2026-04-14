from rest_framework import serializers

from .models import Inquiry


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
