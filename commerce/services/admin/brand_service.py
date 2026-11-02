from django.db.models import Sum

from commerce.models import CommerceStorefrontSettings


class BrandService:

    @staticmethod
    def get_or_create(empresa) -> CommerceStorefrontSettings:
        obj, _ = CommerceStorefrontSettings.objects.get_or_create(empresa=empresa)
        return obj

    @staticmethod
    def update(empresa, form):
        settings = BrandService.get_or_create(empresa)
        bound = form.__class__(form.data, form.files, instance=settings)
        if bound.is_valid():
            bound.save()
        return settings

    @staticmethod
    def summary(empresa) -> dict:
        from commerce.models import CommerceOrder
        settings = BrandService.get_or_create(empresa)
        return {
            "settings": settings,
            "has_logo": bool(settings.logo),
            "storefront_url": "/commerce/",
            "order_count": CommerceOrder.objects.filter(empresa=empresa).count(),
            "pending_orders": CommerceOrder.objects.filter(
                empresa=empresa, status=CommerceOrder.PENDING
            ).count(),
            "revenue_paid": (
                CommerceOrder.objects.filter(
                    empresa=empresa, payment_status=CommerceOrder.PAYMENT_PAID
                ).aggregate(total=Sum("total"))["total"] or 0
            ),
        }
