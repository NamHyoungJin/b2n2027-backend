import logging
from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.mixins import B2nResponseMixin

from .models import Participant
from .serializers import (
    ParticipantSerializer,
    ParticipantListSerializer,
    ParticipantCreateSerializer,
    RefundCalculationSerializer,
)

logger = logging.getLogger(__name__)


class ParticipantViewSet(B2nResponseMixin, viewsets.ModelViewSet):
    """참여자 관리 ViewSet"""

    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = Participant.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'register_type', 'payment_method']
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """액션에 따라 적절한 Serializer 반환"""
        if self.action == 'list':
            return ParticipantListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ParticipantCreateSerializer
        return ParticipantSerializer
    
    def create(self, request, *args, **kwargs):
        """참여자 등록"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 생성된 참여자 정보 전체 반환
        participant = Participant.objects.get(pk=serializer.instance.pk)
        response_serializer = ParticipantSerializer(participant)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        """PUT/PATCH 후 상세는 passport_copy URL 없이 ParticipantSerializer로 반환"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        participant = self.get_object()
        return Response(ParticipantSerializer(participant).data)

    @action(detail=True, methods=['get'])
    def calculate_refund(self, request, pk=None):
        """환불 금액 계산"""
        participant = self.get_object()
        
        # 행사일 설정 (설정 파일로 관리 권장)
        event_date = datetime(2026, 5, 20).date()
        today = timezone.now().date()
        diff_days = (event_date - today).days
        
        total_amount = Decimal('50000')  # 기준 금액
        refund_rate = 0
        
        if diff_days >= 7:
            refund_rate = 100
        elif diff_days >= 3:
            refund_rate = 70
        elif diff_days >= 1:
            refund_rate = 50
        else:
            refund_rate = 0
        
        refund_amount = total_amount * Decimal(refund_rate / 100)
        
        data = {
            'diff_days': diff_days,
            'rate': refund_rate,
            'refund_amount': refund_amount,
            'total_amount': total_amount,
            'status': participant.status,
        }
        
        serializer = RefundCalculationSerializer(data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """상태 변경 (입금 확인, 취소 등)"""
        participant = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Participant.STATUS_CHOICES):
            return Response(
                {'error': '유효하지 않은 상태입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant.status = new_status

        # PAID 상태로 변경 시 QR 코드 자동 생성
        if new_status == 'PAID' and not participant.qr_image:
            logger.info("[QR] change_status -> PAID, generating QR participant_id=%s", participant.pk)
            participant.generate_qr_code()
        elif new_status == 'PAID' and participant.qr_image:
            logger.info("[QR] change_status -> PAID, qr_image already exists participant_id=%s path=%s", participant.pk, participant.qr_image.name)

        participant.save()
        
        serializer = ParticipantSerializer(participant)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        """QR 코드 수동 생성"""
        participant = self.get_object()
        logger.info("[QR] generate_qr action participant_id=%s uuid=%s has_qr=%s", participant.pk, participant.uuid, bool(participant.qr_image))
        participant.generate_qr_code()
        participant.save()
        logger.info("[QR] generate_qr action done participant_id=%s path=%s", participant.pk, participant.qr_image.name if participant.qr_image else None)
        
        serializer = ParticipantSerializer(participant)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """통계 데이터 반환"""
        total_count = Participant.objects.count()
        status_stats = {}
        
        for status_code, status_name in Participant.STATUS_CHOICES:
            count = Participant.objects.filter(status=status_code).count()
            status_stats[status_code] = {
                'name': status_name,
                'count': count
            }
        
        payment_stats = {}
        for payment_code, payment_name in Participant.PAYMENT_CHOICES:
            count = Participant.objects.filter(payment_method=payment_code).count()
            payment_stats[payment_code] = {
                'name': payment_name,
                'count': count
            }
        
        return Response({
            'total_count': total_count,
            'status_stats': status_stats,
            'payment_stats': payment_stats,
        })
    
    @action(detail=False, methods=['get'])
    def verify_qr(self, request):
        """QR 코드 (UUID)로 참여자 확인"""
        uuid = request.query_params.get('uuid')
        
        if not uuid:
            return Response(
                {'error': 'UUID가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            participant = Participant.objects.get(uuid=uuid)
            serializer = ParticipantSerializer(participant)
            return Response(serializer.data)
        except Participant.DoesNotExist:
            return Response(
                {'error': '참여자를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
