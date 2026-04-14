import re

from django.db.models import Q
from rest_framework import serializers

from apps.products.models import ApplicationOptionItem, ProductApplication
from apps.products.serializers import update_product_application_from_payload

from .models import Participant

MAX_PASSPORT_COPY_BYTES = 5 * 1024 * 1024  # 5MB

_KR_MOBILE_DIGITS = re.compile(r"^01\d{8,9}$")


def _phone_digits_only(s: str) -> str:
    return "".join(c for c in (s or "") if c.isdigit())


def normalize_participant_phone(value):
    """저장용: 숫자만, 한국 휴대폰 10~11자리."""
    nd = _phone_digits_only(value or "")
    if not nd:
        raise serializers.ValidationError("연락처를 입력해 주세요.")
    if not _KR_MOBILE_DIGITS.match(nd):
        raise serializers.ValidationError(
            "휴대폰 번호는 010 등으로 시작하는 10~11자리 숫자여야 합니다."
        )
    return nd


class ParticipantSerializer(serializers.ModelSerializer):
    """참여자 전체 정보 Serializer"""

    def validate_phone(self, value):
        return normalize_participant_phone(value)

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    register_type_display = serializers.CharField(source='get_register_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    passport_copy_uploaded = serializers.SerializerMethodField()

    product_application = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    product_application_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Participant
        fields = [
            'id', 'uuid', 'group_id', 'name', 'phone', 'email',
            'passport_english_name', 'passport_number', 'passport_expiry_date', 'resident_registration_number',
            'church_role', 'age_group', 'gender', 'attendee_category', 'country', 'organization',
            'register_type', 'register_type_display',
            'payment_method', 'payment_method_display',
            'status', 'status_display',
            'passport_copy_uploaded',
            'product_application',
            'product_application_detail',
            'qr_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'group_id', 'qr_image', 'created_at', 'updated_at', 'passport_copy_uploaded']

    def get_passport_copy_uploaded(self, obj):
        return bool(getattr(obj, 'passport_copy', None))

    def get_product_application_detail(self, obj):
        app = getattr(obj, 'product_application', None)
        if app is None:
            return None
        prod = app.product
        add = app.additional_product
        lines = []
        for line in ApplicationOptionItem.objects.filter(application=app).select_related("option_item"):
            oi = line.option_item
            lines.append(
                {
                    'id': line.id,
                    'option_item_id': oi.id,
                    'option_name': oi.name,
                    'selected_price': str(line.selected_price),
                }
            )
        return {
            'id': app.id,
            'product': {
                'id': prod.id,
                'name': prod.name,
                'base_price': str(prod.base_price),
                'segment': getattr(prod, 'segment', 'BASIC') or 'BASIC',
            },
            'participation_type': app.participation_type,
            'additional_tier': app.additional_tier,
            'additional_product': (
                {
                    'id': add.id,
                    'name': add.name,
                    'price_a_1n2d': str(add.price_a_1n2d),
                    'price_b_day': str(add.price_b_day),
                }
                if add
                else None
            ),
            'total_amount': str(app.total_amount),
            'option_lines': lines,
            'created_at': app.created_at.isoformat() if app.created_at else None,
        }


class ParticipantListSerializer(serializers.ModelSerializer):
    """참여자 리스트용 간소화 Serializer"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    passport_copy_uploaded = serializers.SerializerMethodField()
    # 연결된 상품 신청 합계 금액(없으면 null)
    total_amount = serializers.SerializerMethodField()
    registration_label = serializers.SerializerMethodField()
    is_group_representative = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            'id', 'name', 'phone', 'email', 'group_id',
            'passport_english_name', 'church_role', 'age_group', 'attendee_category', 'country', 'organization',
            'status', 'status_display',
            'register_type', 'payment_method', 'payment_method_display',
            'passport_copy_uploaded',
            'total_amount',
            'registration_label',
            'is_group_representative',
            'created_at',
        ]

    def get_passport_copy_uploaded(self, obj):
        return bool(getattr(obj, 'passport_copy', None))

    def get_total_amount(self, obj):
        app = getattr(obj, "product_application", None)
        if app is None:
            return None
        return str(app.total_amount)

    def _anchor_id(self, obj):
        return obj.group_id if obj.group_id is not None else obj.pk

    def _member_count_for_anchor(self, obj):
        cache = self.context.setdefault('_group_anchor_member_counts', {})
        aid = self._anchor_id(obj)
        if aid not in cache:
            cache[aid] = Participant.objects.filter(Q(pk=aid) | Q(group_id=aid)).count()
        return cache[aid]

    def get_registration_label(self, obj):
        return '단체' if self._member_count_for_anchor(obj) > 1 else '개인'

    def get_is_group_representative(self, obj):
        if obj.group_id is None or obj.group_id != obj.pk:
            return False
        return self._member_count_for_anchor(obj) > 1


class ParticipantCreateSerializer(serializers.ModelSerializer):
    """참여자 등록용 Serializer (통합 등록 폼 스펙, multipart 시 passport_copy 가능)"""

    passport_copy = serializers.ImageField(required=False, allow_null=True)
    product_application_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
    )
    # 관리자 PATCH — 연결된 ProductApplication을 www 신청과 동일 규칙으로 갱신
    product_application_update = serializers.JSONField(required=False, write_only=True)
    # www 등록 — 휴대폰 SMS 인증 후 발급 토큰(관리자 JWT로 생성 시 생략)
    phone_verification_token = serializers.CharField(
        required=False,
        write_only=True,
        allow_blank=True,
        default='',
    )
    # 단체 등록 2번째 참가자부터 — SMS 인증 생략(www 전용, 관리자 생성 시 무시)
    group_member_without_phone_verification = serializers.BooleanField(
        required=False,
        default=False,
        write_only=True,
    )
    # 단체·엑셀 2번째 참가자부터 — 첫 번째로 등록된 참가자의 participants.id
    anchor_group_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, min_value=1)

    def validate_phone(self, value):
        return normalize_participant_phone(value)

    def validate_anchor_group_id(self, value):
        if value is None:
            return None
        if not Participant.objects.filter(pk=value).exists():
            raise serializers.ValidationError('유효하지 않은 그룹(대표) ID입니다.')
        return value

    class Meta:
        model = Participant
        fields = [
            'name', 'phone', 'email',
            'passport_english_name', 'passport_number', 'passport_expiry_date', 'resident_registration_number',
            'church_role', 'age_group', 'gender', 'attendee_category', 'country', 'organization',
            'register_type', 'payment_method',
            'passport_copy',
            'product_application_id',
            'product_application_update',
            'phone_verification_token',
            'group_member_without_phone_verification',
            'anchor_group_id',
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
        validated_data.pop('product_application_update', None)
        validated_data.pop('phone_verification_token', None)
        validated_data.pop('group_member_without_phone_verification', None)
        anchor_id = validated_data.pop('anchor_group_id', None)
        raw_app_id = validated_data.pop('product_application_id', None)
        instance = super().create(validated_data)
        if anchor_id is not None:
            instance.group_id = anchor_id
        else:
            instance.group_id = instance.pk
        instance.save(update_fields=['group_id'])
        if raw_app_id is not None:
            instance.product_application_id = raw_app_id
            instance.save(update_fields=['product_application'])
        return instance

    def update(self, instance, validated_data):
        validated_data.pop('phone_verification_token', None)
        pa_update = validated_data.pop('product_application_update', None)
        instance = super().update(instance, validated_data)
        if pa_update is not None:
            if not instance.product_application_id:
                raise serializers.ValidationError(
                    {'product_application_update': '연결된 상품 신청이 없습니다. (product_application)'}
                )
            update_product_application_from_payload(instance.product_application, pa_update)
            instance.product_application.refresh_from_db()
        return instance


class RefundCalculationSerializer(serializers.Serializer):
    """환불 금액 계산 응답용 Serializer"""
    
    diff_days = serializers.IntegerField()
    rate = serializers.IntegerField()
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
