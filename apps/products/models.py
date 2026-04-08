from django.db import models


class Product(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "ACTIVE"),
        ("INACTIVE", "INACTIVE"),
    ]

    name = models.CharField(max_length=200, verbose_name="상품명")
    description = models.TextField(blank=True, default="", verbose_name="상품 설명(HTML)")
    base_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="기본 가격")
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

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="option_items",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    price_before = models.DecimalField(max_digits=12, decimal_places=0)
    price_after = models.DecimalField(max_digits=12, decimal_places=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
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

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="applications")
    participation_type = models.CharField(max_length=20, choices=PARTICIPATION_CHOICES)
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
