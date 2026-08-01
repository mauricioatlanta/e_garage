"""
BaseStorefrontImporter — interfaz que todo adaptador debe implementar.

Cada adaptador vive en commerce/importers/<nombre>.py y expone una
clase llamada exactamente `Importer` que extiende esta clase base.

El comando import_storefront descubre y llama al adaptador por nombre:
    python manage.py import_storefront --adapter monteazul --empresa 2

Invariantes:
- El adaptador NUNCA importa SECRET_KEY, credenciales de pago ni datos bancarios.
- El adaptador es idempotente: ejecutarlo dos veces produce el mismo resultado.
- dry_run=True no escribe nada en la base de datos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taller.models import Empresa


@dataclass
class ImportResult:
    settings_created: bool = False
    settings_updated: bool = False
    pages_created: int = 0
    pages_updated: int = 0
    faqs_created: int = 0
    faqs_updated: int = 0
    errors: list[str] = field(default_factory=list)

    def __str__(self):
        cfg = "creada" if self.settings_created else ("actualizada" if self.settings_updated else "sin cambios")
        return (
            f"Configuración: {cfg} | "
            f"Páginas: {self.pages_created} creadas, {self.pages_updated} actualizadas | "
            f"FAQs: {self.faqs_created} creadas, {self.faqs_updated} actualizadas"
        )


class BaseStorefrontImporter:
    """Clase base para adaptadores de storefront."""

    def __init__(self, empresa: "Empresa", *, source: str | None = None, dry_run: bool = False):
        self._empresa = empresa
        self._source = source
        self._dry_run = dry_run

    # ── API pública que el comando llama ─────────────────────────

    def run(self) -> ImportResult:
        result = ImportResult()
        self._import_settings(result)
        page_map = self._import_pages(result)
        self._import_faqs(result, page_map)
        return result

    # ── Métodos que los adaptadores deben sobreescribir ──────────

    def get_settings_data(self) -> dict:
        """Devuelve dict con los campos de CommerceStorefrontSettings."""
        raise NotImplementedError

    def get_pages_data(self) -> list[dict]:
        """Devuelve lista de dicts con los campos de CommerceStaticPage."""
        raise NotImplementedError

    def get_faqs_data(self) -> list[dict]:
        """Devuelve lista de dicts con campos de CommerceFAQ.
        Cada dict puede incluir 'page_slug' para vincular a la página."""
        return []

    # ── Internos ─────────────────────────────────────────────────

    def _import_settings(self, result: ImportResult):
        from commerce.models import CommerceStorefrontSettings

        data = self.get_settings_data()
        if self._dry_run:
            exists = CommerceStorefrontSettings.objects.filter(empresa=self._empresa).exists()
            print(f"  [dry-run] {'ACTUALIZA' if exists else 'CREA'} storefront settings")
            return

        _, created = CommerceStorefrontSettings.objects.update_or_create(
            empresa=self._empresa, defaults=data
        )
        if created:
            result.settings_created = True
        else:
            result.settings_updated = True

    def _import_pages(self, result: ImportResult) -> dict[str, object]:
        """Importa páginas estáticas. Devuelve {slug: CommerceStaticPage}."""
        from commerce.models import CommerceStaticPage

        page_map: dict[str, object] = {}

        for page_data in self.get_pages_data():
            slug = page_data.get("slug") or ""
            if not slug:
                result.errors.append(f"Página sin slug: {page_data.get('title')}")
                continue

            if self._dry_run:
                exists = CommerceStaticPage.objects.filter(
                    empresa=self._empresa, slug=slug
                ).exists()
                print(f"  [dry-run] {'ACTUALIZA' if exists else 'CREA'} página: {slug}")
                continue

            try:
                page, created = CommerceStaticPage.objects.update_or_create(
                    empresa=self._empresa,
                    slug=slug,
                    defaults={k: v for k, v in page_data.items() if k != "slug"},
                )
                page_map[slug] = page
                if created:
                    result.pages_created += 1
                else:
                    result.pages_updated += 1
            except Exception as exc:
                result.errors.append(f"Página '{slug}': {exc}")

        return page_map

    def _import_faqs(self, result: ImportResult, page_map: dict):
        from commerce.models import CommerceFAQ

        for i, faq_data in enumerate(self.get_faqs_data()):
            page_slug = faq_data.pop("page_slug", None)
            page = page_map.get(page_slug) if page_slug else None

            if self._dry_run:
                print(f"  [dry-run] FAQ #{i+1}: {faq_data.get('question', '')[:60]}")
                continue

            try:
                question = faq_data.get("question", "")
                faq, created = CommerceFAQ.objects.update_or_create(
                    empresa=self._empresa,
                    question=question,
                    defaults={**faq_data, "page": page},
                )
                if created:
                    result.faqs_created += 1
                else:
                    result.faqs_updated += 1
            except Exception as exc:
                result.errors.append(f"FAQ '{question[:40]}': {exc}")
