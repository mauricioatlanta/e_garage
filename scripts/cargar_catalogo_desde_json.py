#!/usr/bin/env python3
"""
Script para cargar Catálogo Maestro desde archivo JSON

Este script lee un archivo JSON con la estructura de servicios maestros
y los carga en la base de datos con soporte multi-país y aliases regionales.

OPCIÓN RECOMENDADA: Usar el management command de Django
    python manage.py cargar_catalogo_maestro

OPCIÓN ALTERNATIVA: Ejecutar desde Django shell
    python manage.py shell
    >>> exec(open('scripts/cargar_catalogo_desde_json.py').read())
    >>> cargar_desde_json('scripts/catalogo_maestro_servicios.json')
"""

import os
import json

# Intentar importar Django (si ya está configurado, no necesita setup)
try:
    from django.conf import settings

    if not settings.configured:
        import django

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
        django.setup()
except (ImportError, AttributeError):
    # Si no está configurado, intentar setup
    import django
    import sys

    # Agregar el directorio del proyecto al path
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
    django.setup()

from decimal import Decimal
from taller.models.empresa import Empresa
from taller.servicios.models import (
    Servicio,
    CategoriaServicio,
    CategoriaServicioName,
    ServicioName,
)


def cargar_desde_json(json_path="scripts/catalogo_maestro_servicios.json"):
    """
    Carga el catálogo maestro desde un archivo JSON.

    Args:
        json_path: Ruta al archivo JSON con la estructura de servicios

    Returns:
        str: Mensaje de confirmación con estadísticas
    """
    MASTER_ID = 1

    # Obtener o crear empresa maestra
    try:
        empresa_maestra = Empresa.objects.get(id=MASTER_ID)
    except Empresa.DoesNotExist:
        from django.contrib.auth.models import User

        user_sistema, _ = User.objects.get_or_create(
            username="sistema_catalogo_maestro",
            defaults={"email": "sistema@egarage.com", "is_active": False},
        )
        empresa_maestra = Empresa.objects.create(
            id=MASTER_ID,
            user=user_sistema,
            nombre_taller="Catálogo Maestro Global",
            empresa="Sistema eGarage",
            pais="CL",
            is_trial=False,
        )
        print("✅ Empresa maestra creada")

    # Configuración de países e idiomas
    paises_config = {
        "US": "en",
        "BR": "pt",
        "CL": "es",
        "MX": "es",
        "VE": "es",
        "PE": "es",
        "CO": "es",
        "EC": "es",
        "AR": "es",
        "UY": "es",
    }

    # Mapeo de categorías por país (se crean automáticamente si no existen)
    categorias_config = {
        "mantenimiento": {
            "CL": {
                "label": "Mantenimiento Periódico",
                "aliases": ["mantenimiento", "preventivo", "servicio periódico"],
            },
            "MX": {
                "label": "Mantenimiento Periódico",
                "aliases": ["mantenimiento", "preventivo", "servicio periódico"],
            },
            "AR": {
                "label": "Mantenimiento Periódico",
                "aliases": ["mantenimiento", "preventivo", "service"],
            },
            "UY": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "CO": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "EC": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "PE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "VE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "US": {
                "label": "Preventive Maintenance",
                "aliases": ["maintenance", "preventive", "periodic service"],
            },
            "BR": {
                "label": "Manutenção Periódica",
                "aliases": ["manutenção", "preventivo", "serviço periódico"],
            },
        },
        "bodyshop": {
            "CL": {
                "label": "Desabolladura y Pintura",
                "aliases": ["pintura", "desabollado", "bodyshop", "chapa"],
            },
            "MX": {
                "label": "Desabolladura y Pintura",
                "aliases": ["pintura", "desabollado", "bodyshop", "chapa"],
            },
            "AR": {
                "label": "Chapa y Pintura",
                "aliases": ["chapista", "choque", "bollo", "pintura"],
            },
            "UY": {"label": "Chapa y Pintura", "aliases": ["chapeado", "golpe", "pintura"]},
            "CO": {
                "label": "Latonería y Pintura",
                "aliases": ["golpe", "latas", "pintar", "latonería"],
            },
            "EC": {"label": "Enderezada y Pintura", "aliases": ["choque", "enderezado", "pintura"]},
            "PE": {
                "label": "Desabolladura y Pintura",
                "aliases": ["pintura", "desabollado", "chapa"],
            },
            "VE": {
                "label": "Desabolladura y Pintura",
                "aliases": ["pintura", "desabollado", "chapa"],
            },
            "US": {
                "label": "Bodywork & Paint",
                "aliases": ["paint", "bodywork", "bodyshop", "collision"],
            },
            "BR": {
                "label": "Funilaria e Pintura",
                "aliases": ["pintura", "funilaria", "bodyshop", "chapa"],
            },
        },
        "motor": {
            "CL": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "MX": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "AR": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "UY": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "CO": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "EC": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "PE": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "VE": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "US": {
                "label": "Engine & Transmission",
                "aliases": ["engine", "transmission", "gearbox"],
            },
            "BR": {"label": "Motor e Transmissão", "aliases": ["motor", "transmissão", "câmbio"]},
        },
        "especialidades": {
            "CL": {
                "label": "Servicios Especializados",
                "aliases": ["especializado", "servicios varios"],
            },
            "MX": {
                "label": "Servicios Especializados",
                "aliases": ["especializado", "servicios varios"],
            },
            "AR": {
                "label": "Servicios Especializados",
                "aliases": ["especializado", "servicios varios"],
            },
            "UY": {"label": "Servicios Especializados", "aliases": ["especializado"]},
            "CO": {"label": "Servicios Especializados", "aliases": ["especializado"]},
            "EC": {"label": "Servicios Especializados", "aliases": ["especializado"]},
            "PE": {"label": "Servicios Especializados", "aliases": ["especializado"]},
            "VE": {"label": "Servicios Especializados", "aliases": ["especializado"]},
            "US": {"label": "Specialized Services", "aliases": ["specialized", "various services"]},
            "BR": {"label": "Serviços Especializados", "aliases": ["especializado"]},
        },
    }

    # Leer archivo JSON
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            servicios_data = json.load(f)
    except FileNotFoundError:
        return f"❌ Error: No se encontró el archivo {json_path}"
    except json.JSONDecodeError as e:
        return f"❌ Error: JSON inválido en {json_path}: {e}"

    servicios_creados = 0
    servicios_actualizados = 0
    nombres_creados = 0

    print(f"📖 Leyendo {len(servicios_data)} servicios del archivo JSON...")

    # Procesar cada servicio del JSON
    for item in servicios_data:
        code = item.get("code", "")
        category = item.get("category", "mantenimiento")
        translations = item.get("translations", {})

        if not code or not translations:
            print(f"⚠️  Saltando servicio sin código o traducciones: {item}")
            continue

        # Crear categorías para cada país
        categorias_por_pais = {}
        for country in paises_config.keys():
            if category in categorias_config:
                categoria, _ = CategoriaServicio.objects.get_or_create(
                    code=category, country=country, defaults={"activo": True}
                )

                # Crear nombre de categoría
                if country in categorias_config[category]:
                    cat_info = categorias_config[category][country]
                    language = paises_config[country]

                    CategoriaServicioName.objects.update_or_create(
                        categoria=categoria,
                        language=language,
                        is_default=True,
                        defaults={
                            "label": cat_info["label"],
                            "aliases": cat_info.get("aliases", []),
                        },
                    )

                categorias_por_pais[country] = categoria

        # Obtener nombre base (preferir US, luego CL, luego el primero disponible)
        nombre_base = None
        for preferred in ["US", "CL"]:
            if preferred in translations:
                nombre_base = translations[preferred].get("label")
                break
        if not nombre_base and translations:
            first_country = list(translations.keys())[0]
            nombre_base = translations[first_country].get("label")

        if not nombre_base:
            print(f"⚠️  Saltando servicio {code}: no se encontró nombre base")
            continue

        # Usar la primera categoría disponible como referencia
        primera_categoria = None
        for preferred_country in ["US", "CL"]:
            if preferred_country in categorias_por_pais:
                primera_categoria = categorias_por_pais[preferred_country]
                break
        if not primera_categoria and categorias_por_pais:
            primera_categoria = list(categorias_por_pais.values())[0]

        if not primera_categoria:
            print(f"⚠️  No se pudo crear categoría para {category}, saltando servicio {code}")
            continue

        # Crear o obtener servicio maestro
        servicio, created = Servicio.objects.get_or_create(
            nombre=nombre_base,
            empresa_id=MASTER_ID,
            categoria=primera_categoria,
            defaults={
                "activo": True,
                "precio_base": Decimal("0.00"),
            },
        )

        if created:
            servicios_creados += 1
            print(f"✅ Servicio maestro creado: {nombre_base} ({code})")
        else:
            servicios_actualizados += 1

        # Poblar nombres localizados para todos los países
        for country, language in paises_config.items():
            # Obtener traducción del país o usar fallback
            if country in translations:
                config = translations[country]
            elif "CL" in translations:
                config = translations["CL"]  # Fallback a Chile
            elif "US" in translations:
                config = translations["US"]  # Fallback a USA
            else:
                continue  # Saltar si no hay traducción disponible

            label = config.get("label", "")
            aliases = config.get("aliases", [])

            if not label:
                continue

            # Determinar si es el nombre por defecto para este idioma
            is_default = False
            if language == "es":
                is_default = True
            elif language == "en":
                has_spanish = any(paises_config.get(c, "") == "es" for c in translations.keys())
                is_default = not has_spanish
            elif language == "pt":
                has_spanish = any(paises_config.get(c, "") == "es" for c in translations.keys())
                has_english = any(paises_config.get(c, "") == "en" for c in translations.keys())
                is_default = not has_spanish and not has_english

            # Crear nombre localizado con aliases regionales
            _, name_created = ServicioName.objects.update_or_create(
                servicio=servicio,
                language=language,
                is_default=is_default,
                defaults={
                    "label": label,
                    "aliases": aliases,  # Aliases específicos de la región
                },
            )

            if name_created:
                nombres_creados += 1

            print(f"   🌍 [{country}] {label} - Aliases: {', '.join(aliases[:3])}...")

    total = Servicio.objects.filter(empresa_id=MASTER_ID).count()
    total_nombres = ServicioName.objects.filter(servicio__empresa_id=MASTER_ID).count()

    return f"""
✅ Catálogo maestro cargado desde JSON exitosamente.
📊 Resumen:
   - Servicios procesados del JSON: {len(servicios_data)}
   - Servicios creados: {servicios_creados}
   - Servicios actualizados: {servicios_actualizados}
   - Nombres localizados creados: {nombres_creados}
   - Total servicios en catálogo: {total}
   - Total nombres localizados: {total_nombres}
   - Países soportados: {', '.join(paises_config.keys())}
   
🎯 El catálogo está listo para producción.
   Los usuarios pueden buscar con su jerga local y encontrarán los servicios correctos.
"""


if __name__ == "__main__":
    print("=" * 70)
    print("🌍 CARGANDO CATÁLOGO MAESTRO DESDE JSON")
    print("=" * 70)
    resultado = cargar_desde_json()
    print(resultado)
    print("=" * 70)
