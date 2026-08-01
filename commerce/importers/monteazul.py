"""
Adaptador MonteAzul para import_storefront.

Acepta --source /ruta/al/proyecto/monteazulspa para:
- Validar que la ruta parece un proyecto MonteAzul reconocible.
- Copiar el logo mediante Django storage.
- Cargar contenido real de páginas desde el proyecto fuente.

Sin --source usa defaults hardcodeados (útil para tests y fixtures).

Lo que NUNCA lee ni imprime:
    - settings.py ni .env ni variables de entorno
    - SECRET_KEY, WebPay, credenciales de pago
    - Datos bancarios o contraseñas

Uso:
    python manage.py import_storefront --adapter monteazul --empresa 2
    python manage.py import_storefront --adapter monteazul --empresa 2 \\
        --source /mnt/datos/projecto/monteazulspa --overwrite
    python manage.py import_storefront --adapter monteazul --empresa 2 --dry-run
"""
from __future__ import annotations

import json
from pathlib import Path

from commerce.importers.base import BaseStorefrontImporter

# ── Archivos que indican que el source es un proyecto MonteAzul válido ────────
_SENTINEL_FILES = [
    "manage.py",
    "gestion_taller",
]

# ── Rutas candidatas para el logo dentro del proyecto fuente ──────────────────
_LOGO_CANDIDATES = [
    "media/logomonteazul.png",
    "media/logo.png",
    "static/images/logomonteazul.png",
    "static/images/logo.png",
]

# ── Defaults de arranque (usados si no hay --source o si source no tiene datos) ─

_DEFAULT_SETTINGS = {
    "tagline": "Repuestos de calidad para tu vehículo",
    "font_primary": "Inter",
    "primary_color": "#1E40AF",
    "secondary_color": "#1E3A8A",
    "accent_color": "#0EA5E9",
    "seo_title": "MonteAzul — Repuestos automotrices",
    "seo_description": (
        "Encuentra repuestos originales y alternativos para tu vehículo. "
        "Stock permanente, despacho a todo Chile."
    ),
    "whatsapp_number": "",
    "instagram_url": "",
    "facebook_url": "",
}

_DEFAULT_PAGES = [
    {
        "key": "nosotros",
        "slug": "nosotros",
        "title": "Quiénes somos",
        "body": (
            "MonteAzul es una empresa chilena dedicada a la venta de repuestos automotrices. "
            "Contamos con stock permanente de filtros, lubricantes, frenos y más."
        ),
        "is_active": True,
        "position": 1,
        "meta_title": "Quiénes somos — MonteAzul",
        "meta_description": (
            "Conoce a MonteAzul, empresa chilena de repuestos automotrices con despacho a todo Chile."
        ),
    },
    {
        "key": "faq",
        "slug": "preguntas-frecuentes",
        "title": "Preguntas frecuentes",
        "body": "",
        "is_active": True,
        "position": 2,
        "meta_title": "Preguntas frecuentes — MonteAzul",
        "meta_description": "Resolvemos tus dudas sobre despacho, garantía y compatibilidad de repuestos.",
    },
]

_DEFAULT_FAQS = [
    {
        "page_slug": "preguntas-frecuentes",
        "question": "¿Hacen despacho a todo Chile?",
        "answer": (
            "Sí, despachamos a todo Chile vía Starken y Chilexpress. "
            "El tiempo de entrega es de 2 a 5 días hábiles según la región."
        ),
        "position": 1,
        "is_active": True,
    },
    {
        "page_slug": "preguntas-frecuentes",
        "question": "¿Cómo sé si el repuesto es compatible con mi vehículo?",
        "answer": (
            "Cada producto indica el modelo y año de compatibilidad. "
            "Si tienes dudas, contáctanos con tu patente o número de VIN."
        ),
        "position": 2,
        "is_active": True,
    },
    {
        "page_slug": "preguntas-frecuentes",
        "question": "¿Cuál es la garantía de los productos?",
        "answer": (
            "Todos nuestros productos tienen garantía mínima de 3 meses. "
            "Los productos originales siguen la garantía del fabricante."
        ),
        "position": 3,
        "is_active": True,
    },
    {
        "page_slug": "preguntas-frecuentes",
        "question": "¿Puedo devolver un producto?",
        "answer": (
            "Sí, aceptamos devoluciones dentro de los primeros 7 días corridos "
            "desde la recepción, siempre que el producto no haya sido instalado."
        ),
        "position": 4,
        "is_active": True,
    },
]


class Importer(BaseStorefrontImporter):
    """Adaptador MonteAzul. Descubierto por el comando a través del nombre del módulo."""

    # ── Validación del source ────────────────────────────────────

    def _source_path(self) -> Path | None:
        if not self._source:
            return None
        p = Path(self._source)
        if not p.exists():
            raise FileNotFoundError(f"--source no existe: {self._source}")
        # Verificar que parece un proyecto MonteAzul
        if not all((p / s).exists() for s in _SENTINEL_FILES):
            raise ValueError(
                f"--source '{p}' no parece un proyecto MonteAzul reconocible "
                f"(faltan: {[s for s in _SENTINEL_FILES if not (p / s).exists()]})"
            )
        return p

    def _load_fixture(self) -> dict:
        """Lee storefront_data.json del source si existe; si no, dict vacío."""
        try:
            p = self._source_path()
        except (FileNotFoundError, ValueError):
            return {}
        if p is None:
            return {}
        fixture = p / "storefront_data.json"
        if not fixture.exists():
            return {}
        # Leer solo el archivo de datos; nunca leer settings.py ni .env
        with fixture.open(encoding="utf-8") as f:
            return json.load(f)

    # ── Interfaz pública del adaptador ───────────────────────────

    def get_settings_data(self) -> dict:
        data = self._load_fixture()
        return {**_DEFAULT_SETTINGS, **data.get("settings", {})}

    def get_pages_data(self) -> list[dict]:
        data = self._load_fixture()
        return data.get("pages", _DEFAULT_PAGES)

    def get_faqs_data(self) -> list[dict]:
        data = self._load_fixture()
        raw = data.get("faqs", _DEFAULT_FAQS)
        return [dict(item) for item in raw]

    def find_logo_file(self) -> Path | None:
        try:
            p = self._source_path()
        except (FileNotFoundError, ValueError):
            return None
        if p is None:
            return None
        for candidate in _LOGO_CANDIDATES:
            logo = p / candidate
            if logo.exists():
                return logo
        return None
