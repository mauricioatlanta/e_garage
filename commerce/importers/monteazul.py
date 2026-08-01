"""
Adaptador MonteAzul para import_storefront.

Lee desde un archivo JSON (--source ruta/archivo.json) o usa los
defaults hardcodeados si no se pasa --source.

Lo que NUNCA importa:
    - SECRET_KEY ni variables de entorno
    - Credenciales de WebPay / Flow / MercadoPago
    - Datos bancarios
    - Contraseñas de usuarios

Uso:
    python manage.py import_storefront --adapter monteazul --empresa 2
    python manage.py import_storefront --adapter monteazul --empresa 2 --source datos/monteazul.json
    python manage.py import_storefront --adapter monteazul --empresa 2 --dry-run
"""
from __future__ import annotations

import json
from pathlib import Path

from commerce.importers.base import BaseStorefrontImporter


# ── Datos por defecto de MonteAzul ────────────────────────────────────────────
# Editables en un archivo JSON externo; estos son los valores de arranque.

_DEFAULT_SETTINGS = {
    "tagline": "Repuestos de calidad para tu vehículo",
    "primary_color": "#1E40AF",
    "secondary_color": "#1E3A8A",
    "accent_color": "#0EA5E9",
    "seo_title": "MonteAzul — Repuestos automotrices",
    "seo_description": "Encuentra repuestos originales y alternativos para tu vehículo. Stock permanente, despacho a todo Chile.",
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
        "meta_description": "Conoce a MonteAzul, empresa chilena de repuestos automotrices con despacho a todo Chile.",
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
        "answer": "Sí, despachamos a todo Chile vía Starken y Chilexpress. El tiempo de entrega es de 2 a 5 días hábiles según la región.",
        "position": 1,
        "is_active": True,
    },
    {
        "page_slug": "preguntas-frecuentes",
        "question": "¿Cómo sé si el repuesto es compatible con mi vehículo?",
        "answer": "Cada producto indica el modelo y año de compatibilidad. Si tienes dudas, contáctanos con tu patente o número de VIN.",
        "position": 2,
        "is_active": True,
    },
    {
        "page_slug": "preguntas-frecuentes",
        "question": "¿Cuál es la garantía de los productos?",
        "answer": "Todos nuestros productos tienen garantía mínima de 3 meses. Los productos originales siguen la garantía del fabricante.",
        "position": 3,
        "is_active": True,
    },
    {
        "page_slug": "preguntas-frecuentes",
        "question": "¿Puedo devolver un producto?",
        "answer": "Sí, aceptamos devoluciones dentro de los primeros 7 días corridos desde la recepción, siempre que el producto no haya sido instalado.",
        "position": 4,
        "is_active": True,
    },
]


class Importer(BaseStorefrontImporter):
    """Adaptador MonteAzul. El comando lo descubre por el nombre del módulo."""

    def _load_source(self) -> dict:
        if not self._source:
            return {}
        path = Path(self._source)
        if not path.exists():
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self._source}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def get_settings_data(self) -> dict:
        data = self._load_source()
        return {**_DEFAULT_SETTINGS, **data.get("settings", {})}

    def get_pages_data(self) -> list[dict]:
        data = self._load_source()
        return data.get("pages", _DEFAULT_PAGES)

    def get_faqs_data(self) -> list[dict]:
        data = self._load_source()
        # Devuelve copias para no mutar los defaults al hacer pop("page_slug")
        raw = data.get("faqs", _DEFAULT_FAQS)
        return [dict(item) for item in raw]
