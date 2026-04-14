from django.contrib import admin

from .models import (
    ApplicationOptionItem,
    Product,
    ProductApplication,
    ProductDetailImage,
    ProductOptionItem,
)


class ProductDetailImageInline(admin.TabularInline):
    model = ProductDetailImage
    extra = 0


class ProductOptionItemInline(admin.TabularInline):
    model = ProductOptionItem
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "segment", "base_price", "price_a_1n2d", "price_b_day", "status", "created_at")
    list_filter = ("status", "segment")
    search_fields = ("name",)
    inlines = [ProductDetailImageInline, ProductOptionItemInline]


@admin.register(ProductOptionItem)
class ProductOptionItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "product",
        "audience",
        "choice_tier",
        "price_before",
        "price_after",
        "is_active",
        "sort_order",
    )
    list_filter = ("is_active", "audience", "choice_tier")


@admin.register(ProductApplication)
class ProductApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "participation_type", "total_amount", "created_at")
    list_filter = ("participation_type",)


@admin.register(ApplicationOptionItem)
class ApplicationOptionItemAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "option_item", "selected_price")
