from rest_framework import serializers

from .models import (
    ApplicationOptionItem,
    Product,
    ProductApplication,
    ProductDetailImage,
    ProductOptionItem,
)
from .pricing import compute_total_amount, unit_price_for_option


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
            "base_price",
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
    class Meta:
        model = ProductOptionItem
        fields = (
            "id",
            "name",
            "description",
            "price_before",
            "price_after",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_price_before(self, value):
        if value < 0:
            raise serializers.ValidationError("0 이상이어야 합니다.")
        return value

    def validate_price_after(self, value):
        if value < 0:
            raise serializers.ValidationError("0 이상이어야 합니다.")
        return value


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
            "base_price",
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
            "base_price",
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

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist as e:
            raise serializers.ValidationError({"product_id": "상품을 찾을 수 없습니다."}) from e

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

        active_option_count = ProductOptionItem.objects.filter(
            product_id=product_id, is_active=True
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
            )
            if qs.count() != len(raw_ids):
                raise serializers.ValidationError(
                    {
                        "option_item_ids": "옵션이 없거나 비활성이거나 다른 상품에 속합니다. (§21 옵션 검증)"
                    }
                )
            options = sorted(qs, key=lambda o: raw_ids.index(o.pk))

        attrs["_product"] = product
        attrs["_options"] = options

        client_total = attrs.get("client_total_amount")
        total = compute_total_amount(product, participation_type, options)
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
        participation_type = validated_data["participation_type"]
        client_total = validated_data.pop("client_total_amount", None)
        applicant_email = validated_data.pop("applicant_email", "") or ""
        validated_data.pop("product_id", None)
        validated_data.pop("option_item_ids", None)

        total = compute_total_amount(product, participation_type, options)

        app = ProductApplication.objects.create(
            product=product,
            participation_type=participation_type,
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
