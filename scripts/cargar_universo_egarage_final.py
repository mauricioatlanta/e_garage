#!/usr/bin/env python3
"""
Script Final: Catálogo Maestro "Todo Latam + US"

Este script pobla la base de datos con servicios que incluyen aliases específicos
para todos los países de América Latina y Estados Unidos, resolviendo el problema
de idiosincrasia regional.

Países soportados:
- CL: Chile
- MX: México  
- US: Estados Unidos
- VE: Venezuela
- PE: Perú
- BR: Brasil
- CO: Colombia
- EC: Ecuador
- AR: Argentina
- UY: Uruguay

Uso:
    python manage.py shell
    >>> exec(open('scripts/cargar_universo_egarage_final.py').read())
    >>> cargar_universo_egarage()
"""

import os
import django

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


def cargar_universo_egarage():
    """
    Carga el catálogo maestro universal con terminología regional específica.
    Resuelve el problema de idiosincrasia: "gomería" (AR) = "vulcanización" (CL) = "tire shop" (US)
    """
    MASTER_ID = 1
    
    # Obtener o crear empresa maestra
    try:
        empresa_maestra = Empresa.objects.get(id=MASTER_ID)
    except Empresa.DoesNotExist:
        from django.contrib.auth.models import User
        user_sistema, _ = User.objects.get_or_create(
            username="sistema_catalogo_maestro",
            defaults={"email": "sistema@egarage.com", "is_active": False}
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
    
    # Mapeo de categorías por país
    categorias_config = {
        "mantenimiento": {
            "CL": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo", "servicio periódico"]},
            "MX": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo", "servicio periódico"]},
            "AR": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo", "service"]},
            "UY": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "CO": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "EC": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "PE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "VE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "US": {"label": "Preventive Maintenance", "aliases": ["maintenance", "preventive", "periodic service"]},
            "BR": {"label": "Manutenção Periódica", "aliases": ["manutenção", "preventivo", "serviço periódico"]},
        },
        "bodyshop": {
            "CL": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado", "bodyshop", "chapa"]},
            "MX": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado", "bodyshop", "chapa"]},
            "AR": {"label": "Chapa y Pintura", "aliases": ["chapista", "choque", "bollo", "pintura"]},
            "UY": {"label": "Chapa y Pintura", "aliases": ["chapeado", "golpe", "pintura"]},
            "CO": {"label": "Latonería y Pintura", "aliases": ["golpe", "latas", "pintar", "latonería"]},
            "EC": {"label": "Enderezada y Pintura", "aliases": ["choque", "enderezado", "pintura"]},
            "PE": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado", "chapa"]},
            "VE": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado", "chapa"]},
            "US": {"label": "Bodywork & Paint", "aliases": ["paint", "bodywork", "bodyshop", "collision"]},
            "BR": {"label": "Funilaria e Pintura", "aliases": ["pintura", "funilaria", "bodyshop", "chapa"]},
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
            "US": {"label": "Engine & Transmission", "aliases": ["engine", "transmission", "gearbox"]},
            "BR": {"label": "Motor e Transmissão", "aliases": ["motor", "transmissão", "câmbio"]},
        },
    }
    
    # MATRIZ DE SERVICIOS MAESTROS CON TERMINOLOGÍA REGIONAL
    servicios_maestros = [
        {
            "code": "TIRE_REPAIR",
            "cat": "mantenimiento",
            "local": {
                "CL": {"label": "Vulcanización", "aliases": ["parche", "pinchazo", "neumático", "vulcanizado", "reparación neumático"]},
                "MX": {"label": "Reparación de Llantas", "aliases": ["talacha", "parche", "vulcanizadora", "llantera", "reparación llanta"]},
                "AR": {"label": "Gomería", "aliases": ["parche", "cubierta", "auxilio", "goma", "reparación cubierta"]},
                "UY": {"label": "Gomería", "aliases": ["pinchazo", "cubierta", "parche", "goma"]},
                "CO": {"label": "Montallantas", "aliases": ["despinche", "llanta", "parche", "montallantas", "reparación llanta"]},
                "EC": {"label": "Vulcanizadora", "aliases": ["parche", "llanta", "vulcanización", "reparación llanta"]},
                "PE": {"label": "Vulcanización", "aliases": ["parche", "neumático", "vulcanizado", "reparación neumático"]},
                "VE": {"label": "Vulcanización", "aliases": ["parche", "caucho", "vulcanizado", "reparación caucho"]},
                "US": {"label": "Tire Patch / Repair", "aliases": ["flat tire", "plug", "puncture", "tire repair", "tire shop"]},
                "BR": {"label": "Conserto de Pneu", "aliases": ["furo", "borracharia", "remendo", "reparação pneu"]},
            }
        },
        {
            "code": "BODY_PAINT",
            "cat": "bodyshop",
            "local": {
                "CL": {"label": "Desabolladura y Pintura", "aliases": ["toque", "pintura", "desabollado", "chapa", "abolladura"]},
                "MX": {"label": "Desabolladura y Pintura", "aliases": ["golpe", "pintura", "desabollado", "chapa", "enderezado"]},
                "AR": {"label": "Chapa y Pintura", "aliases": ["chapista", "choque", "bollo", "pintura", "chapa"]},
                "UY": {"label": "Chapa y Pintura", "aliases": ["chapeado", "golpe", "pintura", "chapa"]},
                "CO": {"label": "Latonería y Pintura", "aliases": ["golpe", "latas", "pintar", "latonería", "enderezado"]},
                "EC": {"label": "Enderezada y Pintura", "aliases": ["choque", "enderezado", "pintura", "enderezar"]},
                "PE": {"label": "Desabolladura y Pintura", "aliases": ["golpe", "pintura", "desabollado", "chapa"]},
                "VE": {"label": "Desabolladura y Pintura", "aliases": ["golpe", "pintura", "desabollado", "chapa"]},
                "US": {"label": "Bodywork & Paint", "aliases": ["dent repair", "pdr", "refinish", "bodywork", "paint"]},
                "BR": {"label": "Funilaria e Pintura", "aliases": ["funilaria", "amassado", "pintura", "chapa"]},
            }
        },
        {
            "code": "ENGINE_TUNEUP",
            "cat": "motor",
            "local": {
                "CL": {"label": "Afinamiento de Motor", "aliases": ["limpieza inyectores", "bujías", "afinamiento", "tune up"]},
                "MX": {"label": "Afinación Mayor", "aliases": ["servicio", "bujías", "afinación", "tune up", "servicio mayor"]},
                "AR": {"label": "Puesta a Punto / Service", "aliases": ["afinación", "correa", "service", "puesta a punto", "tune up"]},
                "UY": {"label": "Afinación de Motor", "aliases": ["afinación", "bujías", "tune up", "servicio"]},
                "CO": {"label": "Sincronización de Motor", "aliases": ["afinación", "bujías", "sincronización", "tune up"]},
                "EC": {"label": "ABC de Motor", "aliases": ["mantenimiento", "limpieza", "abc", "tune up"]},
                "PE": {"label": "Afinamiento de Motor", "aliases": ["afinamiento", "bujías", "tune up", "servicio"]},
                "VE": {"label": "Afinamiento de Motor", "aliases": ["afinamiento", "bujías", "tune up", "servicio"]},
                "US": {"label": "Engine Tune-up", "aliases": ["spark plugs", "coils", "tune up", "engine service"]},
                "BR": {"label": "Regulagem de Motor", "aliases": ["regulagem", "velas", "tune up", "serviço motor"]},
            }
        },
        {
            "code": "OIL_CHANGE",
            "cat": "mantenimiento",
            "local": {
                "CL": {"label": "Cambio de Aceite y Filtro", "aliases": ["mantención", "cambio de aceite", "aceite", "lubricación"]},
                "MX": {"label": "Servicio de Aceite", "aliases": ["afinación menor", "afinación", "cambio de aceite", "servicio menor"]},
                "AR": {"label": "Cambio de Aceite", "aliases": ["cambio de aceite", "aceite", "service", "lubricación"]},
                "UY": {"label": "Cambio de Aceite", "aliases": ["cambio de aceite", "aceite", "lubricación"]},
                "CO": {"label": "Cambio de Aceite", "aliases": ["cambio de aceite", "aceite", "lubricación"]},
                "EC": {"label": "Cambio de Aceite", "aliases": ["cambio de aceite", "aceite", "lubricación"]},
                "PE": {"label": "Cambio de Aceite y Filtro", "aliases": ["cambio de aceite", "aceite", "lubricación"]},
                "VE": {"label": "Cambio de Aceite", "aliases": ["cambio de aceite", "aceite", "lubricación"]},
                "US": {"label": "Oil Change", "aliases": ["lube", "oil service", "oil change", "lubrication"]},
                "BR": {"label": "Troca de Óleo", "aliases": ["troca óleo", "óleo", "lubrificação"]},
            }
        },
        {
            "code": "BRAKE_PADS",
            "cat": "mantenimiento",
            "local": {
                "CL": {"label": "Cambio de Pastillas de Freno", "aliases": ["pastillas", "frenos", "pastillas freno"]},
                "MX": {"label": "Cambio de Balatas", "aliases": ["balatas", "frenos", "pastillas", "balatas freno"]},
                "AR": {"label": "Cambio de Pastillas de Freno", "aliases": ["pastillas", "frenos", "pastillas freno"]},
                "UY": {"label": "Cambio de Pastillas de Freno", "aliases": ["pastillas", "frenos"]},
                "CO": {"label": "Cambio de Pastillas de Freno", "aliases": ["pastillas", "frenos"]},
                "EC": {"label": "Cambio de Pastillas de Freno", "aliases": ["pastillas", "frenos"]},
                "PE": {"label": "Cambio de Pastillas de Freno", "aliases": ["pastillas", "frenos"]},
                "VE": {"label": "Cambio de Pastillas de Freno", "aliases": ["pastillas", "frenos"]},
                "US": {"label": "Brake Pads Replacement", "aliases": ["brake pads", "pads", "brakes"]},
                "BR": {"label": "Troca de Pastilhas", "aliases": ["pastilhas", "freios"]},
            }
        },
    ]
    
    servicios_creados = 0
    servicios_actualizados = 0
    
    # Procesar cada servicio maestro
    for item in servicios_maestros:
        cat_code = item["cat"]
        
        # Crear categorías para cada país
        categorias_por_pais = {}
        for country in paises_config.keys():
            if cat_code in categorias_config:
                categoria, _ = CategoriaServicio.objects.get_or_create(
                    code=cat_code,
                    country=country,
                    defaults={"activo": True}
                )
                
                # Crear nombre de categoría
                if country in categorias_config[cat_code]:
                    cat_info = categorias_config[cat_code][country]
                    language = paises_config[country]
                    
                    CategoriaServicioName.objects.update_or_create(
                        categoria=categoria,
                        language=language,
                        is_default=True,
                        defaults={
                            "label": cat_info["label"],
                            "aliases": cat_info.get("aliases", []),
                        }
                    )
                
                categorias_por_pais[country] = categoria
        
        # Crear servicio maestro único (usando nombre base en inglés como referencia)
        # El servicio se crea una vez y luego se le agregan nombres localizados
        nombre_base = item["local"].get("US", {}).get("label") or item["local"].get("CL", {}).get("label") or item["local"].get(list(item["local"].keys())[0], {}).get("label", f"Servicio {item['code']}")
        
        # Usar la primera categoría disponible como referencia (preferir US o CL)
        primera_categoria = None
        for preferred_country in ["US", "CL"]:
            if preferred_country in categorias_por_pais:
                primera_categoria = categorias_por_pais[preferred_country]
                break
        if not primera_categoria and categorias_por_pais:
            primera_categoria = list(categorias_por_pais.values())[0]
        
        if not primera_categoria:
            print(f"⚠️  No se pudo crear categoría para {cat_code}, saltando servicio {item['code']}")
            continue
        
        # Crear o obtener servicio maestro (usando nombre base)
        servicio, created = Servicio.objects.get_or_create(
            nombre=nombre_base,
            empresa_id=MASTER_ID,
            categoria=primera_categoria,
            defaults={
                "activo": True,
                "precio_base": Decimal("0.00"),
            }
        )
        
        if created:
            servicios_creados += 1
            print(f"✅ Servicio maestro creado: {nombre_base} ({item['code']})")
        else:
            servicios_actualizados += 1
        
        # Poblar nombres localizados para todos los países
        for country, language in paises_config.items():
            # Obtener configuración del país o usar fallback
            if country in item["local"]:
                config = item["local"][country]
            elif "CL" in item["local"]:
                config = item["local"]["CL"]  # Fallback a Chile
            elif "US" in item["local"]:
                config = item["local"]["US"]  # Fallback a USA
            else:
                continue  # Saltar si no hay configuración
            
            label = config["label"]
            aliases = config.get("aliases", [])
            
            # Determinar si es el nombre por defecto para este idioma
            # Preferir español si existe, sino inglés, sino portugués
            is_default = False
            if language == "es":
                is_default = True
            elif language == "en":
                # Solo es default si no hay español
                has_spanish = any(paises_config.get(c, "") == "es" for c in item["local"].keys())
                is_default = not has_spanish
            elif language == "pt":
                # Solo es default si no hay español ni inglés
                has_spanish = any(paises_config.get(c, "") == "es" for c in item["local"].keys())
                has_english = any(paises_config.get(c, "") == "en" for c in item["local"].keys())
                is_default = not has_spanish and not has_english
            
            # Crear nombre localizado con aliases regionales
            ServicioName.objects.update_or_create(
                servicio=servicio,
                language=language,
                is_default=is_default,
                defaults={
                    "label": label,
                    "aliases": aliases,  # Aliases específicos de la región
                }
            )
            
            print(f"   🌍 [{country}] {label} - Aliases: {', '.join(aliases[:3])}...")
    
    total = Servicio.objects.filter(empresa_id=MASTER_ID).count()
    
    return f"""
✅ Catálogo maestro universal cargado exitosamente.
📊 Resumen:
   - Servicios creados: {servicios_creados}
   - Servicios actualizados: {servicios_actualizados}
   - Total en catálogo: {total}
   - Países soportados: {', '.join(paises_config.keys())}
   
🎯 Ejemplos de búsqueda regional:
   - AR: "gomería" → encontrará servicios de neumáticos
   - CO: "montallantas" → encontrará servicios de neumáticos
   - MX: "talacha" → encontrará servicios de neumáticos
   - CL: "vulcanización" → encontrará servicios de neumáticos
   - US: "tire shop" → encontrará servicios de neumáticos
   - AR: "bollo" → encontrará servicios de bodyshop
   - CO: "latonería" → encontrará servicios de bodyshop
   - MX: "afinación menor" → encontrará cambio de aceite
   - CL: "mantención" → encontrará cambio de aceite
"""


if __name__ == "__main__":
    print("="*70)
    print("🌍 CARGANDO CATÁLOGO MAESTRO UNIVERSAL - TODO LATAM + US")
    print("="*70)
    resultado = cargar_universo_egarage()
    print(resultado)
    print("="*70)
    print("🎉 ¡Proceso completado! El catálogo está listo para producción.")
    print("="*70)

