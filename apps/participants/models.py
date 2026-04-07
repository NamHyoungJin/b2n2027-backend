import logging
import uuid
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.files import File
from django.db import models
from django.utils import timezone
from PIL import Image

logger = logging.getLogger(__name__)


class Participant(models.Model):
    """이벤트 참여자 모델"""
    
    STATUS_CHOICES = [
        ('PENDING', '입금대기'),
        ('PAID', '등록완료'),
        ('CANCEL_REQ', '환불요청'),
        ('CANCELLED', '취소완료'),
        ('REFUNDED', '환불완료'),
    ]
    
    TYPE_CHOICES = [
        ('PRE', '사전등록'),
        ('ONSITE', '현장등록'),
    ]
    
    PAYMENT_CHOICES = [
        ('BANK', '무통장'),
        ('CARD', '카드'),
        ('CASH', '현금'),
    ]

    VISION_TRIP_CHOICES = [
        ('pre', 'B2N 일정 전'),
        ('post', 'B2N 일정 후'),
        ('none', '선택 안함'),
    ]

    # 기본 정보
    name = models.CharField(
        max_length=50, 
        verbose_name='이름',
        help_text='참가자의 실명을 입력합니다',
        db_comment='참가자의 실명'
    )
    phone = models.CharField(
        max_length=20, 
        verbose_name='전화번호',
        help_text='참가자의 연락 가능한 전화번호 (010-0000-0000 형식)',
        db_comment='참가자의 연락 가능한 전화번호 (010-0000-0000 형식)'
    )
    email = models.EmailField(
        unique=True, 
        verbose_name='이메일',
        help_text='참가자의 이메일 주소 (중복 불가, 로그인 ID로 사용)',
        db_comment='참가자의 이메일 주소 (중복 불가, 로그인 ID로 사용)'
    )
    passport_english_name = models.CharField(
        max_length=100,
        verbose_name='여권 영문명',
        help_text='여권에 표기된 영문 이름',
        db_comment='여권 영문명',
        default='',
    )
    passport_number = models.CharField(
        max_length=50,
        verbose_name='여권번호',
        help_text='여권 번호',
        db_comment='여권번호',
        default='',
    )
    passport_expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='여권 만료일',
        help_text='여권 만료일 (YYYY-MM-DD)',
        db_comment='여권 만료일',
    )
    resident_registration_number = models.CharField(
        max_length=20,
        verbose_name='주민등록번호',
        blank=True,
        default='',
        help_text='여행자 보험 가입용, 투어 종료 후 파기',
        db_comment='주민등록번호 (보험용, 투어 후 파기)',
    )

    # 행사 정보
    church_role = models.CharField(
        max_length=50, 
        verbose_name='직분',
        help_text='교회 내 직분 (예: 목사, 전도사, 장로, 집사, 권사, 성도 등)',
        db_comment='교회 내 직분 (목사, 전도사, 장로, 집사, 권사, 성도 등)'
    )
    age_group = models.CharField(
        max_length=20, 
        verbose_name='연령대',
        help_text='참가자의 연령대 (20대, 30대, 40대, 50대, 60대 이상)',
        db_comment='참가자의 연령대 (20대, 30대, 40대, 50대, 60대 이상)'
    )
    gender = models.CharField(
        max_length=10, 
        verbose_name='성별',
        help_text='참가자의 성별 (남성, 여성)',
        db_comment='참가자의 성별 (남성, 여성)'
    )
    country = models.CharField(
        max_length=50, 
        verbose_name='나라', 
        default='한국',
        help_text='참가자의 국적 또는 거주 국가',
        db_comment='참가자의 국적 또는 거주 국가'
    )
    organization = models.CharField(
        max_length=100, 
        verbose_name='단체', 
        blank=True, 
        default='',
        help_text='소속 교회 또는 단체명 (선택 사항)',
        db_comment='소속 교회 또는 단체명 (선택 사항)'
    )

    # 비전트립
    vision_trip_choice = models.CharField(
        max_length=10,
        choices=VISION_TRIP_CHOICES,
        default='none',
        verbose_name='비전트립 선택',
        help_text='B2N 일정 전/후/선택 안함',
        db_comment='비전트립 선택 (pre/post/none)',
    )
    vision_trip_istanbul = models.BooleanField(
        default=False,
        verbose_name='이스탄불(체류)',
        db_comment='비전트립 이스탄불 선택 여부',
    )
    vision_trip_antioch = models.BooleanField(
        default=False,
        verbose_name='안디옥(디스)',
        db_comment='비전트립 안디옥 선택 여부',
    )
    vision_trip_cappadocia = models.BooleanField(
        default=False,
        verbose_name='갑바도기아',
        db_comment='비전트립 갑바도기아 선택 여부',
    )

    # 상태 관리
    register_type = models.CharField(
        max_length=10, 
        choices=TYPE_CHOICES, 
        default='PRE',
        verbose_name='등록 유형',
        help_text='사전등록 또는 현장등록 구분',
        db_comment='등록 유형 (PRE:사전등록, ONSITE:현장등록)'
    )
    payment_method = models.CharField(
        max_length=10, 
        choices=PAYMENT_CHOICES, 
        default='BANK',
        verbose_name='결제 방식',
        help_text='무통장입금, 카드결제, 현금결제 중 선택',
        db_comment='결제 방식 (BANK:무통장, CARD:카드, CASH:현금)'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name='상태',
        help_text='참가 신청 처리 상태 (입금대기, 등록완료, 환불요청, 취소완료, 환불완료)',
        db_comment='신청 처리 상태 (PENDING:입금대기, PAID:등록완료, CANCEL_REQ:환불요청, CANCELLED:취소완료, REFUNDED:환불완료)'
    )
    
    # 시스템 관리
    uuid = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        verbose_name='고유 ID',
        help_text='참가자의 고유 식별자 (자동 생성, QR 코드에 사용)',
        db_comment='참가자의 고유 식별자 (자동 생성, QR 코드에 사용)'
    )
    qr_image = models.ImageField(
        upload_to='qrcodes/', 
        blank=True, 
        null=True,
        verbose_name='QR 코드',
        help_text='참가자 확인용 QR 코드 이미지 (자동 생성)',
        db_comment='참가자 확인용 QR 코드 이미지 파일 경로'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='생성일',
        help_text='신청서가 등록된 날짜와 시간',
        db_comment='신청서가 등록된 날짜와 시간'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='수정일',
        help_text='정보가 마지막으로 수정된 날짜와 시간',
        db_comment='정보가 마지막으로 수정된 날짜와 시간'
    )

    class Meta:
        db_table = 'participants'
        ordering = ['-created_at']
        verbose_name = '참여자'
        verbose_name_plural = '참여자 목록'

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def generate_qr_code(self):
        """QR 코드 생성"""
        logger.info(
            "[QR] generate_qr_code start participant_id=%s uuid=%s MEDIA_ROOT=%s",
            self.pk, self.uuid, getattr(settings, 'MEDIA_ROOT', None),
        )
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(str(self.uuid))
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # PIL Image를 Django File로 변환
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            file_name = f'qr_{self.uuid}.png'

            self.qr_image.save(file_name, File(buffer), save=False)
            buffer.close()

            logger.info(
                "[QR] generate_qr_code ok participant_id=%s uuid=%s path=%s",
                self.pk, self.uuid, self.qr_image.name,
            )
        except Exception as e:
            logger.exception(
                "[QR] generate_qr_code failed participant_id=%s uuid=%s error=%s",
                self.pk, self.uuid, e,
            )
            raise
