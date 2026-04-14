from django.db import models


class Product(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "ACTIVE"),
        ("INACTIVE", "INACTIVE"),
    ]

    SEGMENT_CHOICES = [
        ("BASIC", "기본상품"),
        ("ADDITIONAL", "추가상품"),
    ]

    name = models.CharField(max_length=200, verbose_name="상품명")
    segment = models.CharField(
        max_length=20,
        choices=SEGMENT_CHOICES,
        default="BASIC",
        verbose_name="구분",
    )
    description = models.TextField(blank=True, default="", verbose_name="상품 설명(HTML)")
    base_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="기본 가격")
    price_a_1n2d = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="가격 A (1박2일)",
    )
    price_b_day = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="가격 B (당일)",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        verbose_name="상태",
    )

    application_start = models.DateTimeField(null=True, blank=True, verbose_name="신청 시작")
    application_end = models.DateTimeField(null=True, blank=True, verbose_name="신청 종료")
    event_start = models.DateTimeField(null=True, blank=True, verbose_name="행사 시작")
    event_end = models.DateTimeField(null=True, blank=True, verbose_name="행사 종료")

    thumbnail = models.ImageField(
        upload_to="products/thumbnails/",
        blank=True,
        null=True,
        verbose_name="썸네일",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        verbose_name = "상품"
        verbose_name_plural = "상품"

    def __str__(self):
        return self.name


class ProductDetailImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="detail_images",
    )
    image = models.ImageField(upload_to="products/detail/")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "product_detail_images"
        ordering = ["sort_order", "id"]


class ProductOptionItem(models.Model):
    """비전트립 코스 옵션 — 행 단위로 price_before / price_after (PlanDoc §12)."""

    AUDIENCE_GLOBAL = "GLOBAL"
    AUDIENCE_KOREA = "KOREA"
    AUDIENCE_CHOICES = [
        (AUDIENCE_GLOBAL, "GLOBAL"),
        (AUDIENCE_KOREA, "KOREA"),
    ]

    TIER_FIRST = "FIRST"
    TIER_SECOND = "SECOND"
    TIER_THIRD = "THIRD"
    CHOICE_TIER_CHOICES = [
        (TIER_FIRST, "FIRST"),
        (TIER_SECOND, "SECOND"),
        (TIER_THIRD, "THIRD"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="option_items",
    )
    name = models.CharField(max_length=200, verbose_name="비전트립 제목")
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="기본 내용",
        help_text="짧은 안내·한 줄 요약(plain text 권장).",
    )
    detail_content = models.TextField(
        blank=True,
        default="",
        verbose_name="상세 내용",
        help_text="TipTap HTML — 공지 본문과 동일 에디터(PlanDoc/board_notice.md).",
    )
    image_s3_key = models.CharField(
        max_length=1024,
        blank=True,
        default="",
        verbose_name="상품 이미지 객체 키",
        help_text="S3 또는 로컬 MEDIA 경로 키 (product-option-items/...). PlanDoc/s3Rules.md",
    )
    image = models.ImageField(
        upload_to="products/option_items/",
        blank=True,
        null=True,
        verbose_name="상품 이미지(레거시)",
    )
    price_before = models.DecimalField(max_digits=12, decimal_places=0)
    price_after = models.DecimalField(max_digits=12, decimal_places=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    audience = models.CharField(
        max_length=10,
        choices=AUDIENCE_CHOICES,
        default=AUDIENCE_GLOBAL,
        verbose_name="표시 구분",
    )
    choice_tier = models.CharField(
        max_length=10,
        choices=CHOICE_TIER_CHOICES,
        default=TIER_FIRST,
        verbose_name="선택 구분(지망)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_option_items"
        ordering = ["sort_order", "id"]
        verbose_name = "상품 옵션(코스)"
        verbose_name_plural = "상품 옵션(코스)"

    def __str__(self):
        return f"{self.name} ({self.product_id})"


class ProductApplication(models.Model):
    """상품 신청 — total_amount는 서버 계산값만 저장 (PlanDoc §15, §19~23)."""

    PARTICIPATION_CHOICES = [
        ("BEFORE_B2N", "BEFORE_B2N"),
        ("AFTER_B2N", "AFTER_B2N"),
        ("NOT_PARTICIPATING", "NOT_PARTICIPATING"),
    ]

    ADDITIONAL_TIER_CHOICES = [
        ("NONE", "NONE"),
        ("ONE_NIGHT_TWO_DAYS", "ONE_NIGHT_TWO_DAYS"),
        ("SAME_DAY", "SAME_DAY"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="applications")
    participation_type = models.CharField(max_length=20, choices=PARTICIPATION_CHOICES)
    additional_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="additional_fee_applications",
        verbose_name="추가 상품(선택)",
    )
    additional_tier = models.CharField(
        max_length=30,
        choices=ADDITIONAL_TIER_CHOICES,
        default="NONE",
        verbose_name="추가 상품 요금 구간",
    )
    total_amount = models.DecimalField(max_digits=14, decimal_places=0)
    client_total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="클라이언트가 보낸 합계(감사·검증용, 신뢰하지 않음)",
    )
    applicant_email = models.EmailField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_applications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Application {self.pk} product={self.product_id}"


class ApplicationOptionItem(models.Model):
    application = models.ForeignKey(
        ProductApplication,
        on_delete=models.CASCADE,
        related_name="option_lines",
    )
    option_item = models.ForeignKey(
        ProductOptionItem,
        on_delete=models.PROTECT,
        related_name="application_lines",
    )
    selected_price = models.DecimalField(max_digits=12, decimal_places=0)

    class Meta:
        db_table = "application_option_items"
        ordering = ["id"]
