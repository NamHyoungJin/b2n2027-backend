"""서버 권위 금액 계산 (PlanDoc §16, §21)."""

from decimal import Decimal

from .models import Product, ProductOptionItem


def unit_price_for_option(option: ProductOptionItem, participation_type: str) -> Decimal:
    if participation_type == "BEFORE_B2N":
        return option.price_before
    if participation_type == "AFTER_B2N":
        return option.price_after
    return Decimal("0")


def compute_total_amount(
    product: Product,
    participation_type: str,
    option_items: list[ProductOptionItem],
) -> Decimal:
    total = product.base_price
    if participation_type == "NOT_PARTICIPATING":
        return total
    for opt in option_items:
        if participation_type == "BEFORE_B2N":
            total += opt.price_before
        elif participation_type == "AFTER_B2N":
            total += opt.price_after
    return total


def additional_line_amount(
    additional_product: Product | None,
    additional_tier: str,
) -> Decimal:
    if not additional_product or additional_tier == "NONE":
        return Decimal("0")
    if additional_tier == "ONE_NIGHT_TWO_DAYS":
        return additional_product.price_a_1n2d
    if additional_tier == "SAME_DAY":
        return additional_product.price_b_day
    return Decimal("0")


def compute_application_total(
    product: Product,
    participation_type: str,
    option_items: list[ProductOptionItem],
    additional_product: Product | None = None,
    additional_tier: str = "NONE",
) -> Decimal:
    base = compute_total_amount(product, participation_type, option_items)
    return base + additional_line_amount(additional_product, additional_tier)
