from rest_framework import serializers

from apps.products.models import ProductApplication

from .models import Participant

MAX_PASSPORT_COPY_BYTES = 5 * 1024 * 1024  # 5MB


class ParticipantSerializer(serializers.ModelSerializer):
    """참여자 전체 정보 Serializer"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    register_type_display = serializers.CharField(source='get_register_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    vision_trip_choice_display = serializers.CharField(source='get_vision_trip_choice_display', read_only=True)
    passport_copy_uploaded = serializers.SerializerMethodField()

    product_application = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Participant
        fields = [
            'id', 'uuid', 'name', 'phone', 'email',
            'passport_english_name', 'passport_number', 'passport_expiry_date', 'resident_registration_number',
            'church_role', 'age_group', 'gender', 'attendee_category', 'country', 'organization',
            'vision_trip_choice', 'vision_trip_choice_display',
            'vision_trip_istanbul', 'vision_trip_antioch', 'vision_trip_cappadocia',
            'register_type', 'register_type_display',
            'payment_method', 'payment_method_display',
            'status', 'status_display',
            'passport_copy_uploaded',
            'product_application',
            'qr_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'qr_image', 'created_at', 'updated_at', 'passport_copy_uploaded']

    def get_passport_copy_uploaded(self, obj):
        return bool(getattr(obj, 'passport_copy', None))


class ParticipantListSerializer(serializers.ModelSerializer):
    """참여자 리스트용 간소화 Serializer"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    passport_copy_uploaded = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            'id', 'name', 'phone', 'email',
            'passport_english_name', 'church_role', 'age_group', 'attendee_category', 'country', 'organization',
            'vision_trip_choice',
            'status', 'status_display',
            'register_type', 'payment_method', 'payment_method_display',
            'passport_copy_uploaded',
            'created_at'
        ]

    def get_passport_copy_uploaded(self, obj):
        return bool(getattr(obj, 'passport_copy', None))


class ParticipantCreateSerializer(serializers.ModelSerializer):
    """참여자 등록용 Serializer (통합 등록 폼 스펙, multipart 시 passport_copy 가능)"""

    passport_copy = serializers.ImageField(required=False, allow_null=True)
    product_application_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Participant
        fields = [
            'name', 'phone', 'email',
            'passport_english_name', 'passport_number', 'passport_expiry_date', 'resident_registration_number',
            'church_role', 'age_group', 'gender', 'attendee_category', 'country', 'organization',
            'vision_trip_choice', 'vision_trip_istanbul', 'vision_trip_antioch', 'vision_trip_cappadocia',
            'register_type', 'payment_method',
            'passport_copy',
            'product_application_id',
        ]

    def validate_passport_copy(self, value):
        if value is None:
            return value
        if value.size > MAX_PASSPORT_COPY_BYTES:
            raise serializers.ValidationError('여권 사본은 5MB 이하 이미지만 업로드할 수 있습니다.')
        return value

    def validate_product_application_id(self, value):
        if value is None:
            return value
        if not ProductApplication.objects.filter(pk=value).exists():
            raise serializers.ValidationError('유효하지 않은 상품 신청 ID입니다.')
        return value

    def create(self, validated_data):
        raw_app_id = validated_data.pop('product_application_id', None)
        instance = super().create(validated_data)
        if raw_app_id is not None:
            instance.product_application_id = raw_app_id
            instance.save(update_fields=['product_application'])
        return instance


class RefundCalculationSerializer(serializers.Serializer):
    """환불 금액 계산 응답용 Serializer"""
    
    diff_days = serializers.IntegerField()
    rate = serializers.IntegerField()
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
