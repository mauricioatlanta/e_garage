from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404

from commerce.models import CommerceCategory, CommerceProduct


class ProductService:

    PAGE_SIZE = 25

    @staticmethod
    def list(empresa, search=None, category_pk=None, published_filter=None, page=1):
        qs = (
            CommerceProduct.objects.filter(empresa=empresa)
            .select_related("repuesto", "category")
            .prefetch_related("images")
            .order_by("repuesto__nombre")
        )
        if search:
            qs = qs.filter(
                Q(repuesto__nombre__icontains=search)
                | Q(repuesto__part_number__icontains=search)
                | Q(slug__icontains=search)
            )
        if category_pk:
            qs = qs.filter(category_id=category_pk)
        if published_filter == "published":
            qs = qs.filter(is_publishable=True)
        elif published_filter == "draft":
            qs = qs.filter(is_publishable=False)
        paginator = Paginator(qs, ProductService.PAGE_SIZE)
        return paginator.get_page(page)

    @staticmethod
    def get(empresa, pk):
        return get_object_or_404(
            CommerceProduct.objects.select_related("repuesto", "category")
            .prefetch_related("images"),
            empresa=empresa,
            pk=pk,
        )

    @staticmethod
    def save_form(form):
        """Persiste un form ya validado (update). Punto único de escritura."""
        return form.save()

    @staticmethod
    def toggle_publishable(empresa, pk):
        product = get_object_or_404(CommerceProduct, empresa=empresa, pk=pk)
        product.is_publishable = not product.is_publishable
        if product.is_publishable and not product.published_at:
            from django.utils import timezone
            product.published_at = timezone.now()
        product.save(update_fields=["is_publishable", "published_at"])
        return product

    @staticmethod
    def bulk_set_publishable(empresa, pks, value: bool):
        qs = CommerceProduct.objects.filter(empresa=empresa, pk__in=pks)
        update_fields = {"is_publishable": value}
        if value:
            from django.utils import timezone
            update_fields["published_at"] = timezone.now()
        return qs.update(**update_fields)

    @staticmethod
    def stats(empresa):
        qs = CommerceProduct.objects.filter(empresa=empresa)
        total = qs.count()
        published = qs.filter(is_publishable=True).count()
        return {
            "total": total,
            "published": published,
            "draft": total - published,
        }

    @staticmethod
    def categories_for_select(empresa):
        return CommerceCategory.objects.filter(empresa=empresa, is_active=True).order_by("name")
