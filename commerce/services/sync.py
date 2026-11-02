"""
SyncCommerceCatalogService

Sincroniza explícitamente el ERP → Commerce.
El ERP nunca actualiza Commerce directamente — siempre pasa por este servicio.
Cuando aparezca el Contract Runtime, este servicio consumirá eventos en lugar de
consultar el ERP directamente (sin cambiar la interfaz pública).

Uso:
    service = SyncCommerceCatalogService(empresa)
    result = service.sync_category(categoria_erp)
    result = service.sync_product(repuesto, publish=True)
    summary = service.sync_all(publish_with_stock=True, dry_run=False)
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.utils.text import slugify

if TYPE_CHECKING:
    from taller.models import Empresa


def _canonical_key(name: str) -> str:
    """Clave canónica para comparar nombres ignorando tildes, mayúsculas y espacios extra."""
    nfkd = unicodedata.normalize("NFKD", name.strip().casefold())
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(stripped.split())


def _has_accents(name: str) -> bool:
    nfkd = unicodedata.normalize("NFKD", name)
    return any(unicodedata.combining(c) for c in nfkd)


@dataclass
class SyncResult:
    categories_created: int = 0
    categories_updated: int = 0
    products_created: int = 0
    products_updated: int = 0
    products_published: int = 0
    errors: list[str] = field(default_factory=list)

    def __str__(self):
        return (
            f"Categorías: {self.categories_created} creadas, {self.categories_updated} actualizadas | "
            f"Productos: {self.products_created} creados, {self.products_updated} actualizados, "
            f"{self.products_published} publicados"
        )


class SyncCommerceCatalogService:

    def __init__(self, empresa: "Empresa"):
        self._empresa = empresa

    # ── API pública ──────────────────────────────────────────────

    def sync_all(self, publish_with_stock: bool = True, dry_run: bool = False) -> SyncResult:
        """Sincroniza todas las categorías y repuestos del tenant."""
        result = SyncResult()
        duplicate_erp = self._sync_categories(result, dry_run)
        self._sync_products(result, publish_with_stock, dry_run, duplicate_erp)
        return result

    def sync_category(self, categoria_erp, dry_run: bool = False) -> "CommerceCategory":
        """Crea o actualiza la CommerceCategory correspondiente a una CategoriaRepuesto."""
        from commerce.models import CommerceCategory

        slug = self._make_category_slug(categoria_erp.nombre)
        defaults = {
            "name": categoria_erp.nombre,
            "meta_title": categoria_erp.nombre,
            "meta_description": f"Repuestos de {categoria_erp.nombre.lower()} disponibles en stock.",
        }

        if dry_run:
            exists = CommerceCategory.objects.filter(
                empresa=self._empresa, categoria_erp=categoria_erp
            ).exists()
            print(f"  [dry-run] {'ACTUALIZA' if exists else 'CREA'} categoría: {categoria_erp.nombre} → slug={slug}")
            return None

        cat, created = CommerceCategory.objects.update_or_create(
            empresa=self._empresa,
            categoria_erp=categoria_erp,
            defaults={**defaults, "slug": slug},
        )
        return cat

    def sync_product(
        self, repuesto, commerce_category=None, publish_with_stock: bool = True, dry_run: bool = False
    ) -> "CommerceProduct":
        """Crea o actualiza el CommerceProduct correspondiente a un Repuesto."""
        from commerce.models import CommerceProduct

        slug = self._make_product_slug(repuesto)
        nombre = repuesto.nombre
        part = repuesto.part_number or ""
        stock = repuesto.cantidad_stock

        is_publishable = publish_with_stock and stock > 0

        meta_title = (f"{nombre} — {part}" if part else nombre)[:70]
        meta_description = self._make_meta_description(repuesto, commerce_category)

        defaults = {
            "category": commerce_category,
            "slug": slug,
            "is_publishable": is_publishable,
            "meta_title": meta_title,
            "meta_description": meta_description,
        }

        if dry_run:
            exists = CommerceProduct.objects.filter(empresa=self._empresa, repuesto=repuesto).exists()
            pub = "PUBLICADO" if is_publishable else "no publicado"
            print(f"  [dry-run] {'ACTUALIZA' if exists else 'CREA'} producto: {nombre} | {pub} | slug={slug}")
            return None

        cp, created = CommerceProduct.objects.update_or_create(
            empresa=self._empresa,
            repuesto=repuesto,
            defaults=defaults,
        )
        return cp

    # ── Internos ─────────────────────────────────────────────────

    def _sync_categories(self, result: SyncResult, dry_run: bool):
        """Sincroniza categorías ERP → Commerce con deduplicación canónica.

        Cuando dos CategoriaRepuesto tienen el mismo nombre salvo tildes/mayúsculas
        (ej. "Electrico" y "Eléctrico"), se elige una como canónica y la otra se
        descarta. Los productos de la categoría descartada se reasignan a la canónica.
        """
        from taller.models.repuesto import CategoriaRepuesto
        from commerce.models import CommerceCategory, CommerceProduct

        erp_cats = list(CategoriaRepuesto.objects.filter(empresa=self._empresa))

        # Agrupar por clave canónica; elegir un ERP-cat por grupo
        canonical_erp: dict[str, object] = {}   # key → CategoriaRepuesto elegida
        duplicate_erp: dict[int, int] = {}       # pk_duplicado → pk_canónico

        for cat_erp in erp_cats:
            key = _canonical_key(cat_erp.nombre)
            existing = canonical_erp.get(key)
            if existing is None:
                canonical_erp[key] = cat_erp
            else:
                winner = self._choose_canonical(existing, cat_erp)
                loser = cat_erp if winner is existing else existing
                canonical_erp[key] = winner
                duplicate_erp[loser.pk] = winner.pk

        # Sincronizar solo los ERP-cats canónicos
        for cat_erp in canonical_erp.values():
            try:
                exists = CommerceCategory.objects.filter(
                    empresa=self._empresa, categoria_erp=cat_erp
                ).exists()
                self.sync_category(cat_erp, dry_run=dry_run)
                if not dry_run:
                    if exists:
                        result.categories_updated += 1
                    else:
                        result.categories_created += 1
            except Exception as exc:
                result.errors.append(f"Categoría {cat_erp.nombre}: {exc}")

        if dry_run or not duplicate_erp:
            return duplicate_erp  # tipo: dict[int, int]

        # Reasignar productos y eliminar CommerceCategorys duplicadas
        for dup_erp_pk, canon_erp_pk in duplicate_erp.items():
            try:
                dup_cc = CommerceCategory.objects.filter(
                    empresa=self._empresa, categoria_erp_id=dup_erp_pk
                ).first()
                canon_cc = CommerceCategory.objects.filter(
                    empresa=self._empresa, categoria_erp_id=canon_erp_pk
                ).first()
                if dup_cc and canon_cc:
                    moved = CommerceProduct.objects.filter(
                        empresa=self._empresa, category=dup_cc
                    ).update(category=canon_cc)
                    if moved:
                        result.errors.append(
                            f"Info: {moved} productos reasignados de '{dup_cc.name}' → '{canon_cc.name}'"
                        )
                    dup_cc.delete()
                elif dup_cc:
                    # Existe la duplicada pero no hay canónica aún (no debería ocurrir)
                    dup_cc.delete()
            except Exception as exc:
                result.errors.append(f"Deduplicación categoría erp_id={dup_erp_pk}: {exc}")
        return duplicate_erp

    def _sync_products(
        self, result: SyncResult, publish_with_stock: bool, dry_run: bool,
        duplicate_erp: "dict[int, int] | None" = None,
    ):
        from taller.models import Repuesto
        from commerce.models import CommerceCategory, CommerceProduct

        category_map = {
            cc.categoria_erp_id: cc
            for cc in CommerceCategory.objects.filter(empresa=self._empresa)
            if cc.categoria_erp_id
        }
        # Extender el mapa con los ERP-cats duplicados → misma CommerceCategory canónica
        if duplicate_erp:
            for dup_pk, canon_pk in duplicate_erp.items():
                if canon_pk in category_map and dup_pk not in category_map:
                    category_map[dup_pk] = category_map[canon_pk]

        for repuesto in Repuesto.objects.filter(empresa=self._empresa).select_related("categoria"):
            try:
                commerce_cat = category_map.get(repuesto.categoria_id) if repuesto.categoria_id else None
                exists = CommerceProduct.objects.filter(empresa=self._empresa, repuesto=repuesto).exists()
                cp = self.sync_product(repuesto, commerce_cat, publish_with_stock, dry_run)
                if not dry_run:
                    if exists:
                        result.products_updated += 1
                    else:
                        result.products_created += 1
                    if cp and cp.is_publishable:
                        result.products_published += 1
            except Exception as exc:
                result.errors.append(f"Repuesto {repuesto.pk} ({repuesto.nombre}): {exc}")

    @staticmethod
    def _choose_canonical(a, b):
        """Elige el CategoriaRepuesto canónico entre dos con mismo nombre normalizado.
        Prefiere el que tiene tildes; en empate, el de menor pk (más antiguo)."""
        a_acc = _has_accents(a.nombre)
        b_acc = _has_accents(b.nombre)
        if a_acc and not b_acc:
            return a
        if b_acc and not a_acc:
            return b
        return a if a.pk <= b.pk else b

    def _make_category_slug(self, nombre: str) -> str:
        from commerce.models import CommerceCategory

        base = slugify(nombre)[:130] or "categoria"
        candidate = base
        suffix = 2
        qs = CommerceCategory.objects.filter(empresa=self._empresa)
        while qs.filter(slug=candidate).exists():
            candidate = f"{base[:125]}-{suffix}"
            suffix += 1
        return candidate

    def _make_product_slug(self, repuesto) -> str:
        from commerce.models import CommerceProduct

        base_source = repuesto.part_number or repuesto.nombre or str(repuesto.pk)
        base = slugify(base_source)[:260] or f"prod-{repuesto.pk}"
        candidate = base
        suffix = 2
        qs = CommerceProduct.objects.filter(empresa=self._empresa).exclude(repuesto=repuesto)
        while qs.filter(slug=candidate).exists():
            candidate = f"{base[:255]}-{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def _make_meta_description(repuesto, commerce_category) -> str:
        cat_name = commerce_category.name if commerce_category else "repuestos"
        nombre = repuesto.nombre
        part = repuesto.part_number
        if part:
            return f"{nombre} (código {part}) — {cat_name} disponible en stock con despacho a todo Chile."[:160]
        return f"{nombre} — {cat_name} disponible en stock con despacho a todo Chile."[:160]
