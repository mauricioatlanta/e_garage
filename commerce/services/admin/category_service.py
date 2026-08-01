from django.db.models import Count
from django.shortcuts import get_object_or_404

from commerce.models import CommerceCategory


class CategoryService:

    @staticmethod
    def list_tree(empresa):
        """
        Árbol completo construido en Python — soporta profundidad arbitraria.
        Cada nodo expone ._resolved_children (lista) y .product_count (int).
        Una sola consulta a la BD, sin importar cuántos niveles tenga el árbol.
        """
        all_cats = list(
            CommerceCategory.objects.filter(empresa=empresa)
            .annotate(product_count=Count("products"))
            .order_by("name")
        )
        cat_map = {c.pk: c for c in all_cats}
        for c in all_cats:
            c._resolved_children = []

        roots = []
        for c in all_cats:
            if c.parent_id is None:
                roots.append(c)
            elif c.parent_id in cat_map:
                cat_map[c.parent_id]._resolved_children.append(c)
        return roots

    @staticmethod
    def list_flat(empresa):
        """Lista plana para selects/dropdowns."""
        return CommerceCategory.objects.filter(empresa=empresa).order_by("name")

    @staticmethod
    def get(empresa, pk):
        return get_object_or_404(CommerceCategory, empresa=empresa, pk=pk)

    @staticmethod
    def create(empresa, form):
        """Persiste la categoría asignando el tenant."""
        category = form.save(commit=False)
        category.empresa = empresa
        category.save()
        return category

    @staticmethod
    def save_form(form):
        """Persiste un form ya validado (update). Punto único de escritura."""
        return form.save()

    @staticmethod
    def toggle_active(empresa, pk):
        cat = get_object_or_404(CommerceCategory, empresa=empresa, pk=pk)
        cat.is_active = not cat.is_active
        cat.save(update_fields=["is_active"])
        return cat

    @staticmethod
    def delete(empresa, pk):
        cat = get_object_or_404(CommerceCategory, empresa=empresa, pk=pk)
        if cat.children.exists():
            raise ValueError(
                f'"{cat.name}" tiene subcategorías. Elimínalas primero.'
            )
        if cat.products.exists():
            count = cat.products.count()
            raise ValueError(
                f'"{cat.name}" tiene {count} producto(s) asociado(s). '
                "Reasígnalos o desasócialos antes de eliminar."
            )
        cat.delete()

    @staticmethod
    def stats(empresa):
        qs = CommerceCategory.objects.filter(empresa=empresa)
        return {
            "total": qs.count(),
            "active": qs.filter(is_active=True).count(),
            "inactive": qs.filter(is_active=False).count(),
        }
