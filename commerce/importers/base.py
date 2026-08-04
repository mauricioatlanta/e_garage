"""
BaseStorefrontImporter — interfaz que todo adaptador debe implementar.

Cada adaptador vive en commerce/importers/<nombre>.py y expone una
clase llamada exactamente `Importer` que extiende esta clase base.

Uso:
    python manage.py import_storefront --adapter monteazul --empresa 2
    python manage.py import_storefront --adapter monteazul --empresa 2 --overwrite
    python manage.py import_storefront --adapter monteazul --empresa 2 --source /ruta/proyecto

Invariantes:
- El adaptador NUNCA importa SECRET_KEY, credenciales de pago ni datos bancarios.
- Sin --overwrite: usa get_or_create (conserva cambios manuales).
- Con --overwrite: usa update_or_create (reemplaza campos).
- dry_run=True no escribe nada en la base de datos ni copia archivos.
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
    pages_skipped: int = 0
    faqs_created: int = 0
    faqs_updated: int = 0
    faqs_skipped: int = 0
    logo_copied: bool = False
    errors: list[str] = field(default_factory=list)

    def __str__(self):
        cfg = "creada" if self.settings_created else ("actualizada" if self.settings_updated else "sin cambios")
        return (
            f"Configuración: {cfg} | "
            f"Páginas: {self.pages_created} creadas, {self.pages_updated} actualizadas, {self.pages_skipped} sin cambios | "
            f"FAQs: {self.faqs_created} creadas, {self.faqs_updated} actualizadas, {self.faqs_skipped} sin cambios"
            + (" | Logo: copiado" if self.logo_copied else "")
        )


class BaseStorefrontImporter:
    """Clase base para adaptadores de storefront."""

    def __init__(
        self,
        empresa: "Empresa",
        *,
        source: str | None = None,
        dry_run: bool = False,
        overwrite: bool = False,
    ):
        self._empresa = empresa
        self._source = source
        self._dry_run = dry_run
        self._overwrite = overwrite

    # ── API pública ──────────────────────────────────────────────

    def run(self) -> ImportResult:
        result = ImportResult()
        self._import_settings(result)
        page_map = self._import_pages(result)
        self._import_faqs(result, page_map)
        self._import_logo(result)
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

    def find_logo_file(self):
        """Devuelve un pathlib.Path al archivo de logo, o None si no hay."""
        return None

    def find_logo_in_storage(self) -> "str | None":
        """Devuelve una ruta relativa al MEDIA_ROOT si el logo ya existe en storage, o None."""
        return None

    # ── Internos ─────────────────────────────────────────────────

    def _import_settings(self, result: ImportResult):
        from commerce.models import CommerceStorefrontSettings

        data = self.get_settings_data()

        if self._dry_run:
            exists = CommerceStorefrontSettings.objects.filter(empresa=self._empresa).exists()
            print(f"  [dry-run] {'ACTUALIZA' if exists else 'CREA'} storefront settings")
            return

        if self._overwrite:
            _, created = CommerceStorefrontSettings.objects.update_or_create(
                empresa=self._empresa, defaults=data
            )
            if created:
                result.settings_created = True
            else:
                result.settings_updated = True
        else:
            _, created = CommerceStorefrontSettings.objects.get_or_create(
                empresa=self._empresa, defaults=data
            )
            result.settings_created = created

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
                defaults = {k: v for k, v in page_data.items() if k != "slug"}
                if self._overwrite:
                    page, created = CommerceStaticPage.objects.update_or_create(
                        empresa=self._empresa, slug=slug, defaults=defaults
                    )
                    page_map[slug] = page
                    if created:
                        result.pages_created += 1
                    else:
                        result.pages_updated += 1
                else:
                    page, created = CommerceStaticPage.objects.get_or_create(
                        empresa=self._empresa, slug=slug, defaults=defaults
                    )
                    page_map[slug] = page
                    if created:
                        result.pages_created += 1
                    else:
                        result.pages_skipped += 1
            except Exception as exc:
                result.errors.append(f"Página '{slug}': {exc}")

        return page_map

    def _import_faqs(self, result: ImportResult, page_map: dict):
        from commerce.models import CommerceFAQ

        for i, faq_data in enumerate(self.get_faqs_data()):
            faq_data = dict(faq_data)  # no mutar el original
            page_slug = faq_data.pop("page_slug", None)
            page = page_map.get(page_slug) if page_slug else None
            question = faq_data.get("question", "")

            if self._dry_run:
                print(f"  [dry-run] FAQ #{i+1}: {question[:60]}")
                continue

            try:
                if self._overwrite:
                    faq, created = CommerceFAQ.objects.update_or_create(
                        empresa=self._empresa,
                        question=question,
                        defaults={**faq_data, "page": page},
                    )
                    if created:
                        result.faqs_created += 1
                    else:
                        result.faqs_updated += 1
                else:
                    faq, created = CommerceFAQ.objects.get_or_create(
                        empresa=self._empresa,
                        question=question,
                        defaults={**faq_data, "page": page},
                    )
                    if created:
                        result.faqs_created += 1
                    else:
                        result.faqs_skipped += 1
            except Exception as exc:
                result.errors.append(f"FAQ '{question[:40]}': {exc}")

    def _import_logo(self, result: ImportResult):
        logo_path = self.find_logo_file()
        # storage fallback solo cuando no hay --source (modo bootstrap sin importación)
        storage_path = None
        if not logo_path and not self._source:
            storage_path = self.find_logo_in_storage()

        if self._dry_run:
            if logo_path:
                print(f"  [dry-run] Copiaría logo: {logo_path}")
            elif storage_path:
                print(f"  [dry-run] Asignaría logo desde storage: {storage_path}")
            return

        if logo_path:
            try:
                from django.core.files import File
                from commerce.models import CommerceStorefrontSettings

                sf = CommerceStorefrontSettings.objects.get(empresa=self._empresa)
                with logo_path.open("rb") as f:
                    sf.logo.save(logo_path.name, File(f), save=True)
                result.logo_copied = True
            except Exception as exc:
                result.errors.append(f"Logo: {exc}")
            return

        if storage_path:
            try:
                from commerce.models import CommerceStorefrontSettings

                sf = CommerceStorefrontSettings.objects.get(empresa=self._empresa)
                if self._overwrite or not sf.logo:
                    sf.logo = storage_path
                    sf.save(update_fields=["logo"])
                    result.logo_copied = True
            except Exception as exc:
                result.errors.append(f"Logo (storage): {exc}")
