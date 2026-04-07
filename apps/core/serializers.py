from rest_framework import serializers


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
