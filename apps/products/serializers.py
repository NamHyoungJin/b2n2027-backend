from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from apps.core.s3_storage import delete_storage_key, image_url_for_key

from .models import (
    ApplicationOptionItem,
    Product,
    ProductApplication,
    ProductDetailImage,
    ProductOptionItem,
)
from .pricing import (
    compute_application_total,
    compute_total_amount,
    unit_price_for_option,
)


class ProductDetailImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDetailImage
        fields = ("id", "image", "sort_order")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")
        if request and instance.image:
            ret["image"] = request.build_absolute_uri(instance.image.url)
        return ret


class ProductListSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "segment",
            "base_price",
            "price_a_1n2d",
            "price_b_day",
            "status",
            "thumbnail_url",
            "created_at",
        )

    def get_thumbnail_url(self, obj):
        if not obj.thumbnail:
            return None
        request = self.context.get("request")
        url = obj.thumbnail.url
        if request:
            return request.build_absolute_uri(url)
        return url


class ProductOptionItemSerializer(serializers.ModelSerializer):
    """
    상품 이미지: `POST /api/board/files/upload/` 로 업로드 후 `image_s3_key` 저장 (PlanDoc/s3Rules.md).
    응답 `image_url`은 Presigned( S3 ) 또는 MEDIA 절대 URL(로컬).
    """

    image_url = serializers.SerializerMethodField(read_only=True)
    image_s3_key = serializers.CharField(required=False, allow_blank=True, max_length=1024)
    clear_image = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = ProductOptionItem
        fields = (
            "id",
            "name",
            "description",
            "detail_content",
            "image_url",
            "image_s3_key",
            "clear_image",
            "price_before",
            "price_after",
            "is_active",
            "sort_order",
            "audience",
            "choice_tier",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_image_url(self, obj):
        if obj.image_s3_key:
            return image_url_for_key(obj.image_s3_key, self.context.get("request"))
        if obj.image:
            request = self.context.get("request")
            url = obj.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def validate_price_before(self, value):
        if value < 0:
            raise serializers.ValidationError("0 이상이어야 합니다.")
        return value

    def validate_price_after(self, value):
        if value < 0:
            raise serializers.ValidationError("0 이상이어야 합니다.")
        return value

    def create(self, validated_data):
        validated_data.pop("clear_image", None)
        validated_data.setdefault("image_s3_key", "")
        instance = super().create(validated_data)
        if instance.image_s3_key:
            ProductOptionItem.objects.filter(pk=instance.pk).update(image=None)
        return instance

    def update(self, instance, validated_data):
        clear_image = validated_data.pop("clear_image", False)
        new_key = validated_data.get("image_s3_key", serializers.empty)

        old_key = (instance.image_s3_key or "").strip()
        had_legacy = bool(instance.image)

        if clear_image:
            if old_key:
                delete_storage_key(old_key)
            if had_legacy:
                instance.image.delete(save=False)
            validated_data["image_s3_key"] = ""
            validated_data["image"] = None
        elif new_key is not serializers.empty:
            nk = (new_key or "").strip()
            if nk != old_key:
                if old_key:
                    delete_storage_key(old_key)
                if had_legacy:
                    instance.image.delete(save=False)
                validated_data["image"] = None
            validated_data["image_s3_key"] = nk

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")
        if request and isinstance(request.user, AnonymousUser):
            ret.pop("image_s3_key", None)
        return ret


class ProductRetrieveSerializer(serializers.ModelSerializer):
    detail_images = ProductDetailImageSerializer(many=True, read_only=True)
    option_items = ProductOptionItemSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "description",
            "segment",
            "base_price",
            "price_a_1n2d",
            "price_b_day",
            "status",
            "application_start",
            "application_end",
            "event_start",
            "event_end",
            "thumbnail_url",
            "detail_images",
            "option_items",
            "created_at",
            "updated_at",
        )

    def get_thumbnail_url(self, obj):
        if not obj.thumbnail:
            return None
        request = self.context.get("request")
        url = obj.thumbnail.url
        if request:
            return request.build_absolute_uri(url)
        return url


class ProductWriteSerializer(serializers.ModelSerializer):
    thumbnail = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = (
            "name",
            "description",
            "segment",
            "base_price",
            "price_a_1n2d",
            "price_b_day",
            "status",
            "application_start",
            "application_end",
            "event_start",
            "event_end",
            "thumbnail",
        )

    def _g(self, attrs, key, default=None):
        if key in attrs:
            return attrs[key]
        if self.instance is not None:
            return getattr(self.instance, key)
        return default

    def validate_base_price(self, value):
        if value < 0:
            raise serializers.ValidationError("기본 가격은 0 이상이어야 합니다.")
        return value

    def validate_price_a_1n2d(self, value):
        if value < 0:
            raise serializers.ValidationError("0 이상이어야 합니다.")
        return value

    def validate_price_b_day(self, value):
        if value < 0:
            raise serializers.ValidationError("0 이상이어야 합니다.")
        return value

    def validate(self, attrs):
        app_s = self._g(attrs, "application_start", None)
        app_e = self._g(attrs, "application_end", None)
        ev_s = self._g(attrs, "event_start", None)
        ev_e = self._g(attrs, "event_end", None)

        if app_s and app_e and app_s > app_e:
            raise serializers.ValidationError({"application_end": "신청 종료일은 신청 시작일 이후여야 합니다."})
        if ev_s and ev_e and ev_s > ev_e:
            raise serializers.ValidationError({"event_end": "행사 종료일은 행사 시작일 이후여야 합니다."})
        if app_e and ev_s and app_e > ev_s:
            raise serializers.ValidationError(
                {"event_start": "행사 시작일은 신청 종료일 이후(또는 같은 시각)인 것이 권장됩니다."}
            )

        return attrs


class ApplicationOptionLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationOptionItem
        fields = ("id", "option_item_id", "selected_price")


class ProductApplicationReadSerializer(serializers.ModelSerializer):
    option_lines = ApplicationOptionLineSerializer(many=True, read_only=True)

    class Meta:
        model = ProductApplication
        fields = (
            "id",
            "product",
            "participation_type",
            "additional_product",
            "additional_tier",
            "total_amount",
            "client_total_amount",
            "applicant_email",
            "option_lines",
            "created_at",
        )


class ProductApplicationCreateSerializer(serializers.Serializer):
    """클라이언트 total_amount는 검증용만 — 저장은 서버 계산값 (§19~22)."""

    product_id = serializers.IntegerField()
    participation_type = serializers.ChoiceField(
        choices=["BEFORE_B2N", "AFTER_B2N", "NOT_PARTICIPATING"]
    )
    option_item_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=list,
    )
    additional_product_id = serializers.IntegerField(required=False, allow_null=True)
    additional_tier = serializers.ChoiceField(
        choices=["NONE", "ONE_NIGHT_TWO_DAYS", "SAME_DAY"],
        default="NONE",
    )
    applicant_email = serializers.EmailField(required=False, allow_blank=True, default="")
    client_total_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=0,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        product_id = attrs["product_id"]
        participation_type = attrs["participation_type"]
        raw_ids = attrs.get("option_item_ids") or []
        tier = attrs.get("additional_tier") or "NONE"

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist as e:
            raise serializers.ValidationError({"product_id": "상품을 찾을 수 없습니다."}) from e

        if getattr(product, "segment", "BASIC") != "BASIC":
            raise serializers.ValidationError(
                {"product_id": "행사 신청은 구분이 «기본상품»인 상품만 선택할 수 있습니다."}
            )

        if participation_type == "NOT_PARTICIPATING" and raw_ids:
            raise serializers.ValidationError(
                {"option_item_ids": "NOT_PARTICIPATING일 때는 옵션을 선택할 수 없습니다."}
            )

        if len(raw_ids) != len(set(raw_ids)):
            raise serializers.ValidationError({"option_item_ids": "option_item_ids에 중복이 있습니다."})

        if len(raw_ids) > 1:
            raise serializers.ValidationError(
                {"option_item_ids": "비전트립 코스는 1개만 선택할 수 있습니다."}
            )

        # 사전등록(www)은 KOREA 옵션만 — GLOBAL은 영문 등 다른 채널용
        _apply_audience = (ProductOptionItem.AUDIENCE_KOREA,)
        active_option_count = ProductOptionItem.objects.filter(
            product_id=product_id,
            is_active=True,
            audience__in=_apply_audience,
        ).count()
        if participation_type in ("BEFORE_B2N", "AFTER_B2N") and active_option_count > 0:
            if len(raw_ids) != 1:
                raise serializers.ValidationError(
                    {"option_item_ids": "비전트립 참여 시 코스를 1개 선택해 주세요."}
                )

        if not raw_ids:
            options = []
        else:
            qs = ProductOptionItem.objects.filter(
                pk__in=raw_ids,
                product_id=product_id,
                is_active=True,
                audience__in=_apply_audience,
            )
            if qs.count() != len(raw_ids):
                raise serializers.ValidationError(
                    {
                        "option_item_ids": "옵션이 없거나 비활성이거나 다른 상품에 속합니다. (§21 옵션 검증)"
                    }
                )
            options = sorted(qs, key=lambda o: raw_ids.index(o.pk))

        additional_product = None
        if tier != "NONE":
            add_id = attrs.get("additional_product_id")
            if not add_id:
                raise serializers.ValidationError(
                    {"additional_product_id": "추가 요금(1박2일/당일)을 선택한 경우 추가 상품이 필요합니다."}
                )
            try:
                additional_product = Product.objects.get(pk=add_id)
            except Product.DoesNotExist as e:
                raise serializers.ValidationError(
                    {"additional_product_id": "추가 상품을 찾을 수 없습니다."}
                ) from e
            if getattr(additional_product, "segment", "") != "ADDITIONAL":
                raise serializers.ValidationError(
                    {"additional_product_id": "추가 요금은 구분이 «추가상품»인 상품만 선택할 수 있습니다."}
                )
            if additional_product.status != "ACTIVE":
                raise serializers.ValidationError(
                    {"additional_product_id": "선택한 추가 상품이 비활성입니다."}
                )
        attrs["_additional_product"] = additional_product

        attrs["_product"] = product
        attrs["_options"] = options

        client_total = attrs.get("client_total_amount")
        total = compute_application_total(
            product,
            participation_type,
            options,
            additional_product,
            tier,
        )
        if client_total is not None and client_total != total:
            raise serializers.ValidationError(
                {
                    "client_total_amount": (
                        f"클라이언트 합계({client_total})와 서버 계산({total})이 일치하지 않습니다."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        product = validated_data.pop("_product")
        options = validated_data.pop("_options")
        additional_product = validated_data.pop("_additional_product", None)
        participation_type = validated_data["participation_type"]
        tier = validated_data.pop("additional_tier", "NONE")
        client_total = validated_data.pop("client_total_amount", None)
        applicant_email = validated_data.pop("applicant_email", "") or ""
        validated_data.pop("product_id", None)
        validated_data.pop("option_item_ids", None)
        validated_data.pop("additional_product_id", None)

        total = compute_application_total(
            product,
            participation_type,
            options,
            additional_product,
            tier,
        )

        app = ProductApplication.objects.create(
            product=product,
            participation_type=participation_type,
            additional_product=additional_product,
            additional_tier=tier,
            total_amount=total,
            client_total_amount=client_total,
            applicant_email=applicant_email,
        )

        for opt in options:
            ApplicationOptionItem.objects.create(
                application=app,
                option_item=opt,
                selected_price=unit_price_for_option(opt, participation_type),
            )

        return app


def update_product_application_from_payload(app: ProductApplication, data: dict) -> ProductApplication:
    """
    관리자·내부용 — 기존 ProductApplication을 동일 검증 규칙으로 갱신하고 금액 재계산.
    `data`는 ProductApplicationCreateSerializer와 동일 키 (client_total_amount 생략 가능).
    """
    payload = {**data}
    if "applicant_email" not in payload:
        payload["applicant_email"] = app.applicant_email or ""

    ser = ProductApplicationCreateSerializer(data=payload)
    ser.is_valid(raise_exception=True)
    vd = ser.validated_data

    product = vd.pop("_product")
    options = vd.pop("_options")
    additional_product = vd.pop("_additional_product", None)
    participation_type = vd["participation_type"]
    tier = vd.pop("additional_tier", "NONE")
    vd.pop("client_total_amount", None)
    vd.pop("product_id", None)
    vd.pop("option_item_ids", None)
    vd.pop("additional_product_id", None)
    vd.pop("applicant_email", None)

    total = compute_application_total(
        product,
        participation_type,
        options,
        additional_product,
        tier,
    )

    app.product = product
    app.participation_type = participation_type
    app.additional_product = additional_product
    app.additional_tier = tier
    app.total_amount = total
    app.client_total_amount = None
    app.save()

    ApplicationOptionItem.objects.filter(application=app).delete()
    for opt in options:
        ApplicationOptionItem.objects.create(
            application=app,
            option_item=opt,
            selected_price=unit_price_for_option(opt, participation_type),
        )

    return app
