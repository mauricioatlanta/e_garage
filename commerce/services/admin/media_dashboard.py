"""
MediaDashboardService — agrega el estado del sistema multimedia del Commerce Engine.

Lee:
  - manual_review.json  (generado por el importer: missing + ambiguous)
  - image_index.json    (generado por build_image_index: inventario de disco)
  - ProductImage        (registros en BD: imágenes ya adjuntas a productos)

Devuelve un snapshot estructurado para la vista Media Dashboard.

Convención de rutas por defecto:
  MEDIA_ROOT/commerce/manual_review.json
  MEDIA_ROOT/commerce/image_index.json

Sobreescribibles con:
  settings.COMMERCE_MEDIA_REVIEW_PATH
  settings.COMMERCE_IMAGE_INDEX_PATH
"""
from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings


def _default_review_path() -> Path:
    custom = getattr(settings, "COMMERCE_MEDIA_REVIEW_PATH", None)
    if custom:
        return Path(custom)
    return Path(settings.MEDIA_ROOT) / "commerce" / "manual_review.json"


def _default_index_path() -> Path:
    custom = getattr(settings, "COMMERCE_IMAGE_INDEX_PATH", None)
    if custom:
        return Path(custom)
    return Path(settings.MEDIA_ROOT) / "commerce" / "image_index.json"


class MediaDashboardService:

    def __init__(self, empresa):
        self._empresa = empresa

    # ── Carga de archivos ─────────────────────────────────────────

    def load_review(self, path: Path | None = None) -> dict | None:
        path = path or _default_review_path()
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def load_index_meta(self, path: Path | None = None) -> dict | None:
        path = path or _default_index_path()
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("_meta") or {}
        except (json.JSONDecodeError, OSError):
            return None

    # ── Estado de imágenes adjuntas (ProductImage en BD) ─────────

    def product_image_stats(self) -> dict:
        """
        Cuenta las ProductImages del tenant y detecta archivos rotos en disco.
        Solo verifica existencia de archivo — no carga el contenido.
        """
        from commerce.models import ProductImage

        qs = ProductImage.objects.filter(
            commerce_product__empresa=self._empresa
        ).select_related("commerce_product__repuesto")

        total = qs.count()
        broken = []

        for img in qs:
            try:
                if not img.image.storage.exists(img.image.name):
                    broken.append({
                        "pk": img.pk,
                        "name": img.image.name,
                        "product": str(img.commerce_product),
                        "product_pk": img.commerce_product_id,
                    })
            except Exception:
                broken.append({
                    "pk": img.pk,
                    "name": getattr(img.image, "name", "—"),
                    "product": str(img.commerce_product),
                    "product_pk": img.commerce_product_id,
                })

        return {
            "total": total,
            "ok": total - len(broken),
            "broken": len(broken),
            "broken_list": broken,
        }

    # ── Vista consolidada ─────────────────────────────────────────

    def summary(self) -> dict:
        review = self.load_review()
        index_meta = self.load_index_meta()
        product_images = self.product_image_stats()

        review_path = _default_review_path()
        index_path = _default_index_path()

        raw_missing = (review or {}).get("missing", [])
        missing_enriched = [
            {"db_path": p, "filename": Path(p).name}
            for p in raw_missing
        ]

        return {
            "review": {
                "found": review is not None,
                "path": str(review_path),
                "data": review or {},
                "missing_count": len(raw_missing),
                "ambiguous_count": len((review or {}).get("ambiguous", [])),
                "generated_at": (review or {}).get("generated_at"),
                "missing": missing_enriched,
                "ambiguous": (review or {}).get("ambiguous", []),
            },
            "index": {
                "found": index_meta is not None,
                "path": str(index_path),
                "meta": index_meta or {},
                "total_files": (index_meta or {}).get("total_files", 0),
                "unique_names": (index_meta or {}).get("unique_names", 0),
                "ambiguous_names": (index_meta or {}).get("ambiguous_names", 0),
                "generated_at": (index_meta or {}).get("generated_at"),
            },
            "product_images": product_images,
        }
