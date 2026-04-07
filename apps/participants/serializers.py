from rest_framework import serializers
from .models import Participant


class ParticipantSerializer(serializers.ModelSerializer):
    """참여자 전체 정보 Serializer"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    register_type_display = serializers.CharField(source='get_register_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    vision_trip_choice_display = serializers.CharField(source='get_vision_trip_choice_display', read_only=True)
    
    class Meta:
        model = Participant
        fields = [
            'id', 'uuid', 'name', 'phone', 'email',
            'passport_english_name', 'passport_number', 'passport_expiry_date', 'resident_registration_number',
            'church_role', 'age_group', 'gender', 'country', 'organization',
            'vision_trip_choice', 'vision_trip_choice_display',
            'vision_trip_istanbul', 'vision_trip_antioch', 'vision_trip_cappadocia',
            'register_type', 'register_type_display',
            'payment_method', 'payment_method_display',
            'status', 'status_display',
            'qr_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'qr_image', 'created_at', 'updated_at']


class ParticipantListSerializer(serializers.ModelSerializer):
    """참여자 리스트용 간소화 Serializer"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Participant
        fields = [
            'id', 'name', 'phone', 'email',
            'passport_english_name', 'church_role', 'age_group', 'country', 'organization',
            'vision_trip_choice',
            'status', 'status_display',
            'register_type', 'payment_method', 'payment_method_display',
            'created_at'
        ]


class ParticipantCreateSerializer(serializers.ModelSerializer):
    """참여자 등록용 Serializer (통합 등록 폼 스펙)"""
    
    class Meta:
        model = Participant
        fields = [
            'name', 'phone', 'email',
            'passport_english_name', 'passport_number', 'passport_expiry_date', 'resident_registration_number',
            'church_role', 'age_group', 'gender', 'country', 'organization',
            'vision_trip_choice', 'vision_trip_istanbul', 'vision_trip_antioch', 'vision_trip_cappadocia',
            'register_type', 'payment_method'
        ]


class RefundCalculationSerializer(serializers.Serializer):
    """환불 금액 계산 응답용 Serializer"""
    
    diff_days = serializers.IntegerField()
    rate = serializers.IntegerField()
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
