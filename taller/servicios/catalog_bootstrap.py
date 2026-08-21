from __future__ import annotations

import json
import logging
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError

from .models import CategoriaServicio, CategoriaServicioName, Servicio, ServicioName

logger = logging.getLogger(__name__)

LANGUAGE_BY_COUNTRY = {
    "CL": "es",
    "MX": "es",
    "VE": "es",
    "PE": "es",
    "US": "en",
    "BR": "pt",
}

CATEGORY_ORDER = {
    "mantenimiento": 10,
    "bodyshop": 20,
    "motor": 30,
    "especialidades": 40,
}

CATEGORY_CONFIG = {
    "mantenimiento": {
        "CL": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
        "MX": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
        "VE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
        "PE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
        "US": {"label": "Preventive Maintenance", "aliases": ["maintenance", "preventive"]},
        "BR": {"label": "Manutenção Periódica", "aliases": ["manutenção", "preventivo"]},
    },
    "bodyshop": {
        "CL": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado"]},
        "MX": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado"]},
        "VE": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado"]},
        "PE": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado"]},
        "US": {"label": "Bodywork & Paint", "aliases": ["paint", "bodywork"]},
        "BR": {"label": "Funilaria e Pintura", "aliases": ["pintura", "funilaria"]},
    },
    "motor": {
        "CL": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
        "MX": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
        "VE": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
        "PE": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
        "US": {"label": "Engine & Transmission", "aliases": ["engine", "transmission"]},
        "BR": {"label": "Motor e Transmissão", "aliases": ["motor", "transmissão", "câmbio"]},
    },
    "especialidades": {
        "CL": {"label": "Servicios Especializados", "aliases": ["especializado"]},
        "MX": {"label": "Servicios Especializados", "aliases": ["especializado"]},
        "VE": {"label": "Servicios Especializados", "aliases": ["especializado"]},
        "PE": {"label": "Servicios Especializados", "aliases": ["especializado"]},
        "US": {"label": "Specialized Services", "aliases": ["specialized"]},
        "BR": {"label": "Serviços Especializados", "aliases": ["especializado"]},
    },
}

TYPE_LABELS = {
    "es": "Interno",
    "en": "In-shop",
    "pt": "Interno",
}


@lru_cache(maxsize=1)
def _load_master_catalog():
    json_path = Path(settings.BASE_DIR) / "scripts" / "catalogo_maestro_servicios.json"
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("No se encontró el catálogo maestro de servicios en %s", json_path)
    except json.JSONDecodeError:
        logger.exception("No se pudo leer el catálogo maestro de servicios en %s", json_path)
    return []


def _normalize_country_code(value):
    return (str(value or "CL").upper() or "CL")[:2]


def _get_category_config(category_code, country_code):
    category_info = CATEGORY_CONFIG.get(category_code, {})
    config = category_info.get(country_code) or category_info.get("CL") or {}
    label = (config.get("label") or category_code.replace("_", " ").title()).strip()
    aliases = config.get("aliases") or []
    return label, aliases


def _get_translation(item, country_code):
    translations = item.get("translations") or {}
    if not translations:
        return {}
    return (
        translations.get(country_code)
        or translations.get("CL")
        or translations.get("US")
        or next(iter(translations.values()), {})
    )


def get_master_catalog_service_items(
    country_code,
    *,
    language=None,
    query="",
    category_code="",
    subcategory_code="",
    limit=50,
):
    country_code = _normalize_country_code(country_code)
    language = language or LANGUAGE_BY_COUNTRY.get(country_code, "es")
    category_code = (category_code or "").strip()
    subcategory_code = (subcategory_code or "").strip()
    query_text = (query or "").strip().lower()

    if subcategory_code:
        return []

    items = []
    for item in _load_master_catalog():
        item_category_code = (item.get("category") or "").strip() or "especialidades"
        if category_code and item_category_code != category_code:
            continue

        translation = _get_translation(item, country_code)
        nombre = (translation.get("label") or "").strip()
        aliases = [str(alias or "").strip() for alias in (translation.get("aliases") or []) if alias]
        codigo = (item.get("code") or "").strip()
        categoria, _aliases = _get_category_config(item_category_code, country_code)

        if not nombre:
            continue

        if query_text:
            haystack = " ".join(
                part
                for part in [nombre, codigo, categoria, " ".join(aliases)]
                if part
            ).lower()
            if query_text not in haystack:
                continue

        items.append(
            {
                "id": "",
                "pk": "",
                "nombre": nombre,
                "label": nombre,
                "text": nombre,
                "descripcion": "",
                "codigo_interno": codigo,
                "categoria": categoria,
                "categoria_code": item_category_code,
                "subcategoria": "",
                "subcategoria_code": "",
                "precio": 0.0,
                "precio_base": 0.0,
                "precio_sugerido": 0.0,
                "precio_cliente": 0.0,
                "tipo": TYPE_LABELS.get(language, TYPE_LABELS["es"]),
            }
        )

        if limit and len(items) >= limit:
            break

    return items


def ensure_company_services_catalog(empresa, country_code):
    # Solo debe invocarse desde flujos explícitos y controlados (management
    # command, admin action). Nunca desde una vista GET: escribiría en la BD
    # como efecto lateral de una lectura.
    if not empresa or not getattr(empresa, "pk", None):
        return 0

    country_code = _normalize_country_code(country_code or getattr(empresa, "pais", None))
    if Servicio.objects.filter(
        empresa=empresa,
        categoria__country=country_code,
        activo=True,
    ).exists():
        return 0

    lock_key = f"eg:bootstrap:servicios:{empresa.pk}:{country_code}"
    if not cache.add(lock_key, "1", 30):
        return 0

    try:
        catalog = _load_master_catalog()
        if not catalog:
            return 0

        language = LANGUAGE_BY_COUNTRY.get(country_code, "es")
        categories = {}
        for category_code, order in CATEGORY_ORDER.items():
            label, aliases = _get_category_config(category_code, country_code)
            categoria, _ = CategoriaServicio.objects.get_or_create(
                country=country_code,
                code=category_code,
                defaults={"activo": True, "orden": order},
            )
            update_fields = []
            if categoria.orden != order:
                categoria.orden = order
                update_fields.append("orden")
            if not categoria.activo:
                categoria.activo = True
                update_fields.append("activo")
            if update_fields:
                categoria.save(update_fields=update_fields)

            CategoriaServicioName.objects.update_or_create(
                categoria=categoria,
                language=language,
                is_default=True,
                defaults={"label": label[:100], "aliases": aliases},
            )
            categories[category_code] = categoria

        created_count = 0
        for item in catalog:
            code = (item.get("code") or "").strip()
            category_code = (item.get("category") or "").strip() or "especialidades"
            categoria = categories.get(category_code)
            translation = _get_translation(item, country_code)
            nombre = (translation.get("label") or "").strip()
            aliases = translation.get("aliases") or []

            if not (code and categoria and nombre):
                continue

            servicio, created = Servicio.objects.update_or_create(
                empresa=empresa,
                categoria=categoria,
                codigo_interno=code[:50],
                defaults={
                    "nombre": nombre[:160],
                    "descripcion": "",
                    "precio_base": Decimal("0.00"),
                    "activo": True,
                },
            )
            ServicioName.objects.update_or_create(
                servicio=servicio,
                language=language,
                is_default=True,
                defaults={"label": nombre[:100], "aliases": aliases},
            )
            if created:
                created_count += 1

        return created_count
    except DatabaseError:
        logger.exception(
            "No se pudo bootstrapear el catálogo de servicios para empresa=%s país=%s",
            getattr(empresa, "pk", None),
            country_code,
        )
        return 0
    finally:
        cache.delete(lock_key)
