"""
CommerceCatalogGateway — interfaz estable entre las vistas de Commerce y la fuente de datos.

Sprint 1: implementación directa sobre CommerceProduct + Repuesto (ERP).
Sprint 3: esta implementación se reemplaza por consumo del Contract Runtime.
Las vistas de Commerce llaman solo a este Gateway; nunca importan modelos del ERP.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404

from commerce.models import CommerceCategory, CommerceProduct


class CommerceCatalogGateway:

    def __init__(self, empresa):
        self._empresa = empresa

    # ── Categorías ──────────────────────────────────────────────

    def get_categories(self, parent=None):
        """Devuelve categorías activas del tenant. Sin parent → nivel raíz."""
        qs = CommerceCategory.objects.filter(empresa=self._empresa, is_active=True)
        if parent is None:
            qs = qs.filter(parent__isnull=True)
        else:
            qs = qs.filter(parent=parent)
        return qs.order_by("name")

    def get_category(self, slug):
        return get_object_or_404(
            CommerceCategory,
            empresa=self._empresa,
            slug=slug,
            is_active=True,
        )

    # ── Productos ────────────────────────────────────────────────

    def get_product(self, slug):
        return get_object_or_404(
            CommerceProduct.objects.select_related("repuesto", "category")
                                   .prefetch_related("images"),
            empresa=self._empresa,
            slug=slug,
            is_publishable=True,
        )

    def list_products(self, category=None, limit=None, exclude_product=None):
        """Lista productos publicables del tenant, opcionalmente filtrados por categoría."""
        qs = (
            CommerceProduct.objects.filter(empresa=self._empresa, is_publishable=True)
            .select_related("repuesto", "category")
            .prefetch_related("images")
            .order_by("repuesto__nombre")
        )
        if category is not None:
            category_ids = self._category_tree_ids(category)
            qs = qs.filter(category_id__in=category_ids)
        if exclude_product is not None:
            qs = qs.exclude(pk=exclude_product.pk)
        if limit:
            qs = qs[:limit]
        return qs

    def search(self, query):
        """Búsqueda por nombre, part_number o slug."""
        if not query:
            return CommerceProduct.objects.none()
        return (
            CommerceProduct.objects.filter(empresa=self._empresa, is_publishable=True)
            .filter(
                Q(repuesto__nombre__icontains=query)
                | Q(repuesto__part_number__icontains=query)
                | Q(slug__icontains=query)
            )
            .select_related("repuesto", "category")
            .prefetch_related("images")
            .order_by("repuesto__nombre")
        )

    # ── Internos ─────────────────────────────────────────────────

    def _category_tree_ids(self, category):
        """IDs de la categoría y todas sus subcategorías (recursivo)."""
        ids = [category.pk]
        for child in category.children.filter(is_active=True):
            ids.extend(self._category_tree_ids(child))
        return ids
