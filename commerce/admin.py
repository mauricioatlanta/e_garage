from django.contrib import admin

from commerce.models import (
    CommerceCart,
    CommerceCartItem,
    CommerceCategory,
    CommerceFAQ,
    CommerceOrder,
    CommerceOrderItem,
    CommerceProduct,
    CommerceStorefrontSettings,
    CommerceStaticPage,
    ProductImage,
)


# ── Carrito ───────────────────────────────────────────────────────────────────

class CommerceCartItemInline(admin.TabularInline):
    model = CommerceCartItem
    extra = 0
    readonly_fields = ["product", "quantity"]


@admin.register(CommerceCart)
class CommerceCartAdmin(admin.ModelAdmin):
    list_display = ["empresa", "session_key", "created_at", "updated_at"]
    list_filter = ["empresa"]
    readonly_fields = ["session_key", "created_at", "updated_at"]
    inlines = [CommerceCartItemInline]


# ── Pedidos ───────────────────────────────────────────────────────────────────

class CommerceOrderItemInline(admin.TabularInline):
    model = CommerceOrderItem
    extra = 0
    readonly_fields = ["product", "sku", "name", "unit_price", "quantity"]


@admin.register(CommerceOrder)
class CommerceOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "empresa", "customer_name", "customer_email", "status", "total", "created_at"]
    list_filter = ["empresa", "status"]
    search_fields = ["order_number", "customer_name", "customer_email"]
    readonly_fields = ["order_number", "session_key", "total", "created_at", "updated_at"]
    inlines = [CommerceOrderItemInline]


# ── Catálogo ─────────────────────────────────────────────────────────────────

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(CommerceProduct)
class CommerceProductAdmin(admin.ModelAdmin):
    list_display = ["__str__", "empresa", "category", "is_publishable", "created_at"]
    list_filter = ["empresa", "is_publishable", "category"]
    search_fields = ["repuesto__nombre", "repuesto__part_number", "slug"]
    readonly_fields = ["slug", "created_at", "updated_at"]
    inlines = [ProductImageInline]


@admin.register(CommerceCategory)
class CommerceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "empresa", "parent", "is_active"]
    list_filter = ["empresa", "is_active"]
    search_fields = ["name", "slug"]


# ── Storefront ────────────────────────────────────────────────────────────────

@admin.register(CommerceStorefrontSettings)
class CommerceStorefrontSettingsAdmin(admin.ModelAdmin):
    list_display = ["empresa", "tagline", "font_primary", "schema_version", "updated_at"]
    list_filter = ["empresa"]
    readonly_fields = ["schema_version", "created_at", "updated_at"]


class CommerceFAQInline(admin.TabularInline):
    model = CommerceFAQ
    extra = 0


@admin.register(CommerceStaticPage)
class CommerceStaticPageAdmin(admin.ModelAdmin):
    list_display = ["title", "empresa", "key", "slug", "is_active", "position"]
    list_filter = ["empresa", "key", "is_active"]
    inlines = [CommerceFAQInline]
