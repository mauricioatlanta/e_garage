from django.contrib import admin

from commerce.models import (
    CommerceCart,
    CommerceCartItem,
    CommerceCategory,
    CommerceFAQ,
    CommerceOrder,
    CommerceOrderItem,
    CommercePaymentTransaction,
    CommerceProduct,
    CommerceStorefrontSettings,
    CommerceStaticPage,
    PaymentAttempt,
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
    list_display = [
        "order_number", "empresa", "customer_name", "customer_email",
        "status", "payment_status", "total", "created_at",
    ]
    list_filter = ["empresa", "status", "payment_status"]
    search_fields = ["order_number", "customer_name", "customer_email"]
    readonly_fields = [
        "order_number", "session_key", "total",
        "payment_status", "payment_method", "payment_gateway_ref", "paid_at",
        "created_at", "updated_at",
    ]
    inlines = [CommerceOrderItemInline]


# ── Pagos (solo lectura) ──────────────────────────────────────────────────────

class _ReadOnlyAdmin(admin.ModelAdmin):
    """Base para registros de auditoría: sin add, change ni delete desde admin."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        return {}


@admin.register(CommercePaymentTransaction)
class CommercePaymentTransactionAdmin(_ReadOnlyAdmin):
    list_display = [
        "order", "empresa", "gateway", "status", "amount", "currency",
        "card_last4", "created_at",
    ]
    list_filter = ["empresa", "gateway", "status", "created_at"]
    search_fields = ["order__order_number", "gateway_ref", "gateway_token"]
    readonly_fields = [
        "empresa", "order", "gateway", "gateway_token", "gateway_ref",
        "status", "amount", "currency", "raw_response", "card_last4",
        "confirmed_at", "created_at", "updated_at",
    ]


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(_ReadOnlyAdmin):
    list_display = [
        "order", "empresa", "attempt_number", "gateway", "status", "amount",
        "raw_status", "created_at",
    ]
    list_filter = ["empresa", "gateway", "status", "created_at"]
    search_fields = ["order__order_number", "gateway_ref", "gateway_token"]
    readonly_fields = [
        "empresa", "order", "attempt_number", "gateway", "status", "amount",
        "gateway_token", "gateway_ref", "raw_status", "error_code",
        "error_message", "metadata", "completed_at", "created_at", "updated_at",
    ]


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
