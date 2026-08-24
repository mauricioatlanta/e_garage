from __future__ import annotations

import json
import logging
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError

from .models import (
    CategoriaServicio,
    CategoriaServicioName,
    Servicio,
    ServicioName,
    ServicioRubro,
)

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


SERVICE_CATALOG_MATRIX_PATH = Path(settings.BASE_DIR) / "scripts" / "service_catalog_matrix_v1.json"

SERVICE_CATALOG_COUNTRIES = {
    "AR",
    "BR",
    "CL",
    "CO",
    "EC",
    "MX",
    "PE",
    "US",
    "UY",
    "VE",
}

SERVICE_CATALOG_ALLOWED_STATUSES = {
    "direct",
    "draft_review",
}

SERVICE_CATALOG_EXCLUDED_RUBROS = {
    "PARTS",
    "DESARMADURIA",
    "RECYCLING",
    "MIXED",
}


@lru_cache(maxsize=1)
def load_service_catalog_matrix():
    """
    Carga y valida el catálogo runtime curado de 111 servicios.

    Este catálogo cubre únicamente servicios/mano de obra.
    PARTS, DESARMADURIA, RECYCLING y MIXED quedan fuera por diseño.
    """
    data = json.loads(SERVICE_CATALOG_MATRIX_PATH.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("service catalog matrix debe ser una lista")

    if len(data) != 111:
        raise ValueError(f"service catalog matrix esperaba 111 filas, recibió {len(data)}")

    codes = set()
    edges = set()

    for index, row in enumerate(data, 1):
        required = {"candidate_code", "category", "rubros", "translations"}
        missing = required - set(row)
        if missing:
            raise ValueError(f"fila {index}: faltan campos {sorted(missing)}")

        code = row["candidate_code"]
        if not code or len(code) > 50:
            raise ValueError(f"fila {index}: candidate_code inválido")

        if code in codes:
            raise ValueError(f"candidate_code duplicado: {code}")
        codes.add(code)

        rubros = row.get("rubros") or []
        if not rubros:
            raise ValueError(f"{code}: sin rubros")

        forbidden = set(rubros) & SERVICE_CATALOG_EXCLUDED_RUBROS
        if forbidden:
            raise ValueError(f"{code}: rubros fuera de alcance {sorted(forbidden)}")

        for rubro in rubros:
            edges.add((code, rubro))

        translations = row["translations"]
        if set(translations) != SERVICE_CATALOG_COUNTRIES:
            raise ValueError(f"{code}: países inválidos en translations")

        cl = translations["CL"]
        if not cl.get("label"):
            raise ValueError(f"{code}: falta label CL")

    if len(edges) != 711:
        raise ValueError(f"service catalog matrix esperaba 711 edges, recibió {len(edges)}")

    return tuple(data)


def normalize_company_rubros(config):
    """
    Retorna rubros canónicos de ConfiguracionEmpresa.

    La migración 0177 normaliza datos legacy persistidos.
    Este fallback defensivo evita depender de datos perfectos.
    """
    aliases = {
        "DESARME": "DESARMADURIA",
        "REPUESTOS": "PARTS",
        "CASA_REPUESTOS": "PARTS",
    }

    values = list(config.rubros or [])

    if not values and config.rubro_principal:
        values = [config.rubro_principal]

    return {aliases.get(value, value) for value in values if value}


def select_applicable_catalog_rows(company_rubros):
    """
    Selecciona candidatos cuya aplicabilidad multi-rubro intersecta
    los rubros activos de la empresa.
    """
    wanted = set(company_rubros or [])

    if not wanted:
        return tuple()

    return tuple(row for row in load_service_catalog_matrix() if set(row["rubros"]) & wanted)


def choose_country_translation(row, country_code):
    """
    Devuelve traducción local aprobada.
    Si está pending/no existe, usa explícitamente CL como fallback.
    """
    cc = (country_code or "CL").upper()

    cl = row["translations"]["CL"]

    if cc == "CL":
        return {
            "country_code": "CL",
            "language": "es",
            "label": cl["label"],
            "aliases": cl.get("aliases") or [],
            "source": "CL",
        }

    local = row["translations"].get(cc) or {}

    if local.get("status") in SERVICE_CATALOG_ALLOWED_STATUSES and local.get("label"):
        return {
            "country_code": cc,
            "language": LANGUAGE_BY_COUNTRY.get(cc, "es"),
            "label": local["label"],
            "aliases": local.get("aliases") or [],
            "source": cc,
        }

    return {
        "country_code": "CL",
        "language": "es",
        "label": cl["label"],
        "aliases": cl.get("aliases") or [],
        "source": "CL_FALLBACK",
    }


def _get_or_create_matrix_category(country_code, category_code):
    """
    Crea categorías técnicas de la matriz de forma idempotente.
    Se mantienen separadas por país usando CategoriaServicio.country.
    """
    categoria, _ = CategoriaServicio.objects.get_or_create(
        country=(country_code or "CL").upper(),
        code=category_code,
        defaults={"activo": True},
    )

    language = LANGUAGE_BY_COUNTRY.get((country_code or "CL").upper(), "es")
    CategoriaServicioName.objects.get_or_create(
        categoria=categoria,
        language=language,
        is_default=True,
        defaults={"label": category_code.replace("_", " ").title()},
    )

    return categoria


def sync_company_service_catalog(empresa, country_code=None):
    """
    Materializa/re-sincroniza el catálogo curado para una empresa.

    - Solo procesa candidatos que intersectan config.rubros.
    - Usa candidate_code como identidad idempotente por empresa.
    - Conserva precio_base existente.
    - Crea todos los ServicioRubro del candidato seleccionado.
    - Crea nombre CL y variante del país cuando exista una traducción
      direct/draft_review.
    - No toca servicios custom cuyo codigo_interno no pertenezca a la matriz.
    - No desactiva todavía servicios por rubros removidos; esa política queda
      para una fase posterior.
    """
    from taller.models import ConfiguracionEmpresa

    try:
        config = ConfiguracionEmpresa.objects.get(empresa=empresa)
    except ConfiguracionEmpresa.DoesNotExist:
        return {"created": 0, "updated": 0, "selected": 0}

    cc = (country_code or getattr(empresa, "pais", None) or "CL").upper()

    company_rubros = normalize_company_rubros(config)
    rows = select_applicable_catalog_rows(company_rubros)

    created_count = 0
    updated_count = 0

    for row in rows:
        code = row["candidate_code"]
        local = choose_country_translation(row, cc)
        category = _get_or_create_matrix_category(cc, row["category"])

        servicio, created = Servicio.objects.get_or_create(
            empresa=empresa,
            codigo_interno=code,
            defaults={
                "nombre": local["label"],
                "descripcion": "",
                "precio_base": 0,
                "activo": True,
                "categoria": category,
            },
        )

        if created:
            created_count += 1
        else:
            changed = False

            if not servicio.activo:
                servicio.activo = True
                changed = True

            if servicio.categoria_id != category.id:
                servicio.categoria = category
                changed = True

            if changed:
                servicio.save(update_fields=["activo", "categoria"])
                updated_count += 1

        # Guardar TODOS los rubros curados del candidato, no solo la
        # intersección con la empresa. Esto preserva la cardinalidad original.
        desired_rubros = set(row["rubros"])

        existing_rubros = set(
            ServicioRubro.objects.filter(servicio=servicio).values_list("rubro", flat=True)
        )

        missing_rubros = desired_rubros - existing_rubros

        if missing_rubros:
            ServicioRubro.objects.bulk_create(
                [ServicioRubro(servicio=servicio, rubro=rubro) for rubro in sorted(missing_rubros)],
                ignore_conflicts=True,
            )

        # CL siempre existe como fuente base.
        cl = row["translations"]["CL"]

        ServicioName.objects.update_or_create(
            servicio=servicio,
            country_code="CL",
            language="es",
            is_default=True,
            defaults={
                "label": cl["label"],
                "aliases": cl.get("aliases") or [],
            },
        )

        # Variante local solo cuando existe evidencia aprobada.
        if cc != "CL":
            raw_local = row["translations"].get(cc) or {}

            if raw_local.get("status") in SERVICE_CATALOG_ALLOWED_STATUSES and raw_local.get("label"):
                ServicioName.objects.update_or_create(
                    servicio=servicio,
                    country_code=cc,
                    language=LANGUAGE_BY_COUNTRY.get(cc, "es"),
                    is_default=True,
                    defaults={
                        "label": raw_local["label"],
                        "aliases": raw_local.get("aliases") or [],
                    },
                )

    return {
        "created": created_count,
        "updated": updated_count,
        "selected": len(rows),
    }
