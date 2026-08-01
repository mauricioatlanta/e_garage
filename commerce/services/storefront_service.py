"""
CommerceStorefrontService — resuelve la identidad visual completa de un tenant.

Contrato de la interfaz pública:
    brand = CommerceStorefrontService.resolve(empresa)

Devuelve un dict plano que los templates consumen directamente;
ningún template necesita importar modelos ni consultar Empresa.

Garantías de seguridad:
- Los colores solo se exponen si pasan la validación #RRGGBB.
- La fuente solo se expone si está en la allowlist; si no, cae a "system-ui".
- El servicio nunca crea registros automáticamente.
- Con empresa=None o sin settings, devuelve un fallback seguro (nunca 500).
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taller.models import Empresa

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

ALLOWED_FONTS = frozenset({"Outfit", "Inter", "Roboto", "system-ui"})
FALLBACK_FONT = "system-ui"

_FALLBACK_COLORS = {
    "primary": "#3B82F6",
    "secondary": "#1E40AF",
    "accent": "#06B6D4",
}

_FALLBACK_BRAND: dict = {
    "storefront": None,
    "brand_name": "",
    "logo_url": None,
    "favicon_url": None,
    "tagline": "",
    "colors": _FALLBACK_COLORS,
    "font_primary": FALLBACK_FONT,
    "meta_title": "",
    "meta_description": "",
    "whatsapp": {"number": "", "url": ""},
    "social": {"instagram_url": "", "facebook_url": ""},
    "static_pages": [],
}


class CommerceStorefrontService:

    @classmethod
    def resolve(cls, empresa: "Empresa | None") -> dict:
        """Devuelve el contexto de marca completo para el tenant dado."""
        static_pages: list[dict] = []
        sf = None

        if empresa is not None:
            from commerce.models import CommerceStaticPage, CommerceStorefrontSettings

            sf = (
                CommerceStorefrontSettings.objects
                .filter(empresa=empresa)
                .first()
            )
            static_pages = list(
                CommerceStaticPage.objects
                .filter(empresa=empresa, is_active=True)
                .order_by("position", "title")
                .values("slug", "title", "key")
            )

        brand_name = empresa.nombre if empresa else ""

        if sf is None:
            return {
                **_FALLBACK_BRAND,
                "brand_name": brand_name,
                "meta_title": brand_name,
                "static_pages": static_pages,
            }

        logo_url = sf.logo.url if sf.logo else None
        favicon_url = sf.favicon.url if sf.favicon else None
        whatsapp = sf.whatsapp_number or ""

        return {
            "storefront": sf,
            "brand_name": brand_name,
            "logo_url": logo_url,
            "favicon_url": favicon_url,
            "tagline": sf.tagline,
            "colors": {
                "primary": cls._safe_color(sf.primary_color, _FALLBACK_COLORS["primary"]),
                "secondary": cls._safe_color(sf.secondary_color, _FALLBACK_COLORS["secondary"]),
                "accent": cls._safe_color(sf.accent_color, _FALLBACK_COLORS["accent"]),
            },
            "font_primary": cls._safe_font(sf.font_primary),
            "meta_title": sf.seo_title or brand_name,
            "meta_description": sf.seo_description,
            "whatsapp": {
                "number": whatsapp,
                "url": cls._whatsapp_url(whatsapp),
            },
            "social": {
                "instagram_url": sf.instagram_url,
                "facebook_url": sf.facebook_url,
            },
            "static_pages": static_pages,
        }

    # ── Validadores ──────────────────────────────────────────────

    @staticmethod
    def _safe_color(value: str, fallback: str) -> str:
        if value and _HEX_RE.match(value):
            return value
        return fallback

    @staticmethod
    def _safe_font(value: str) -> str:
        if value in ALLOWED_FONTS:
            return value
        return FALLBACK_FONT

    @staticmethod
    def _whatsapp_url(number: str) -> str:
        if not number:
            return ""
        digits = re.sub(r"[^\d+]", "", number)
        return f"https://wa.me/{digits.lstrip('+')}"
