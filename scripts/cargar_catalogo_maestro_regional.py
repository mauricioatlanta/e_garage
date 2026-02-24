#!/usr/bin/env python3
"""
Script para cargar Catálogo Maestro con Aliases Regionales Específicos

Este script resuelve el desafío de idiosincrasia regional cargando servicios
con aliases específicos por país. Por ejemplo:
- CL: "Cambio de aceite" con alias "mantención"
- MX: "Servicio de aceite" con alias "afinación menor"
- US: "Oil Change" con alias "lube"

Uso:
    python manage.py shell
    >>> exec(open('scripts/cargar_catalogo_maestro_regional.py').read())
    >>> poblar_catalogo_regional()
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


def poblar_catalogo_regional():
    """
    Pobla el catálogo maestro con servicios que tienen aliases regionales específicos.
    Resuelve el desafío de idiosincrasia: "afinación" en MX = "cambio de aceite" en CL = "oil change" en US
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
        print(f"✅ Empresa maestra creada")
    
    # CATÁLOGO CON ALIASES REGIONALES ESPECÍFICOS
    # Estructura: código_maestro -> {países -> {label, aliases}}
    catalogo_regional = {
        "MAINT_OIL_CHANGE": {
            "code": "MAINT_OIL_CHANGE",
            "categoria": "mantenimiento",
            "CL": {
                "label": "Cambio de Aceite y Filtro",
                "aliases": ["mantención", "cambio de aceite", "aceite", "lubricación", "mantenimiento básico"]
            },
            "MX": {
                "label": "Servicio de Aceite",
                "aliases": ["afinación menor", "afinación", "cambio de aceite", "servicio menor", "aceite y filtro"]
            },
            "US": {
                "label": "Oil Change",
                "aliases": ["lube", "oil service", "oil change", "lubrication", "oil filter change"]
            },
            "PE": {
                "label": "Cambio de Aceite y Filtro",
                "aliases": ["mantenimiento", "cambio de aceite", "aceite", "servicio básico"]
            },
            "VE": {
                "label": "Cambio de Aceite y Filtro",
                "aliases": ["mantenimiento", "cambio de aceite", "aceite", "servicio básico"]
            },
            "BR": {
                "label": "Troca de Óleo e Filtro",
                "aliases": ["troca óleo", "óleo", "manutenção básica", "troca filtro"]
            }
        },
        "MAINT_SYNTHETIC_OIL": {
            "code": "MAINT_SYNTHETIC_OIL",
            "categoria": "mantenimiento",
            "CL": {
                "label": "Cambio de Aceite Sintético",
                "aliases": ["aceite sintético", "sintético", "full synthetic", "aceite premium"]
            },
            "MX": {
                "label": "Servicio de Aceite Sintético",
                "aliases": ["aceite sintético", "sintético", "servicio premium", "aceite full synthetic"]
            },
            "US": {
                "label": "Full Synthetic Oil Change",
                "aliases": ["synthetic oil", "full synthetic", "premium oil", "synthetic lube"]
            },
            "PE": {
                "label": "Cambio de Aceite Sintético",
                "aliases": ["aceite sintético", "sintético", "aceite premium"]
            },
            "VE": {
                "label": "Cambio de Aceite Sintético",
                "aliases": ["aceite sintético", "sintético", "aceite premium"]
            },
            "BR": {
                "label": "Troca de Óleo Sintético",
                "aliases": ["óleo sintético", "sintético", "óleo premium"]
            }
        },
        "BRAKE_PADS_FRONT": {
            "code": "BRAKE_PADS_FRONT",
            "categoria": "frenos",
            "CL": {
                "label": "Cambio de Pastillas de Freno Delanteras",
                "aliases": ["pastillas delanteras", "frenos delanteros", "pastillas", "frenos"]
            },
            "MX": {
                "label": "Cambio de Balatas Delanteras",
                "aliases": ["balatas delanteras", "frenos delanteros", "balatas", "frenos", "pastillas"]
            },
            "US": {
                "label": "Front Brake Pads Replacement",
                "aliases": ["front pads", "front brakes", "brake pads", "front brake pads"]
            },
            "PE": {
                "label": "Cambio de Pastillas de Freno Delanteras",
                "aliases": ["pastillas delanteras", "frenos delanteros", "pastillas"]
            },
            "VE": {
                "label": "Cambio de Pastillas de Freno Delanteras",
                "aliases": ["pastillas delanteras", "frenos delanteros", "pastillas"]
            },
            "BR": {
                "label": "Troca de Pastilhas Dianteiras",
                "aliases": ["pastilhas dianteiras", "freios dianteiros", "pastilhas"]
            }
        },
        "TIRE_ROTATION": {
            "code": "TIRE_ROTATION",
            "categoria": "mantenimiento",
            "CL": {
                "label": "Rotación de Neumáticos",
                "aliases": ["rotación", "rotar neumáticos", "cambio posición llantas", "rotación llantas"]
            },
            "MX": {
                "label": "Rotación de Llantas",
                "aliases": ["rotación", "rotar llantas", "cambio posición", "rotación neumáticos"]
            },
            "US": {
                "label": "Tire Rotation",
                "aliases": ["rotation", "tire rotation", "rotate tires", "wheel rotation"]
            },
            "PE": {
                "label": "Rotación de Neumáticos",
                "aliases": ["rotación", "rotar neumáticos", "cambio posición"]
            },
            "VE": {
                "label": "Rotación de Cauchos",
                "aliases": ["rotación", "rotar cauchos", "cambio posición", "rotación gomas"]
            },
            "BR": {
                "label": "Rotação de Pneus",
                "aliases": ["rotação", "rotar pneus", "troca posição", "rotação rodas"]
            }
        },
        "TIRE_SERVICE": {
            "code": "TIRE_SERVICE",
            "categoria": "especialidades",
            "CL": {
                "label": "Vulcanización",
                "aliases": ["vulcanización", "parche neumático", "reparación neumático", "vulcanizado"]
            },
            "MX": {
                "label": "Llantera",
                "aliases": ["llantera", "reparación llanta", "parche llanta", "vulcanización", "servicio llantas"]
            },
            "US": {
                "label": "Tire Shop Service",
                "aliases": ["tire shop", "tire repair", "tire patch", "tire service", "tire fix"]
            },
            "PE": {
                "label": "Vulcanización",
                "aliases": ["vulcanización", "parche neumático", "reparación neumático"]
            },
            "VE": {
                "label": "Vulcanización",
                "aliases": ["vulcanización", "parche caucho", "reparación caucho"]
            },
            "BR": {
                "label": "Vulcanização",
                "aliases": ["vulcanização", "remendo pneu", "reparação pneu"]
            }
        },
        "ALIGNMENT": {
            "code": "ALIGNMENT",
            "categoria": "especialidades",
            "CL": {
                "label": "Alineación y Balanceo",
                "aliases": ["alineación", "balanceo", "alinear", "balancear", "geometría"]
            },
            "MX": {
                "label": "Alineación y Balanceo",
                "aliases": ["alineación", "balanceo", "alinear", "balancear", "geometría"]
            },
            "US": {
                "label": "Wheel Alignment",
                "aliases": ["alignment", "wheel alignment", "front end alignment", "4-wheel alignment"]
            },
            "PE": {
                "label": "Alineación y Balanceo",
                "aliases": ["alineación", "balanceo", "alinear", "balancear"]
            },
            "VE": {
                "label": "Alineación y Balanceo",
                "aliases": ["alineación", "balanceo", "alinear", "balancear"]
            },
            "BR": {
                "label": "Alinhamento e Balanceamento",
                "aliases": ["alinhamento", "balanceamento", "alinhar", "balancear"]
            }
        },
        "AC_RECHARGE": {
            "code": "AC_RECHARGE",
            "categoria": "especialidades",
            "CL": {
                "label": "Carga de Gas Refrigerante",
                "aliases": ["gas", "recarga aire", "aire acondicionado", "gas refrigerante", "r134a"]
            },
            "MX": {
                "label": "Recarga de Gas para Aire Acondicionado",
                "aliases": ["gas", "recarga aire", "aire", "gas refrigerante", "r134a", "clima"]
            },
            "US": {
                "label": "A/C System Recharge",
                "aliases": ["ac recharge", "refrigerant", "ac gas", "air conditioning", "r134a"]
            },
            "PE": {
                "label": "Carga de Gas Refrigerante",
                "aliases": ["gas", "recarga aire", "aire acondicionado", "gas refrigerante"]
            },
            "VE": {
                "label": "Carga de Gas Refrigerante",
                "aliases": ["gas", "recarga aire", "aire acondicionado", "gas refrigerante"]
            },
            "BR": {
                "label": "Recarga de Gás Refrigerante",
                "aliases": ["gás", "recarga ar", "ar condicionado", "gás refrigerante"]
            }
        },
        "ENGINE_CLEANING": {
            "code": "ENGINE_CLEANING",
            "categoria": "estetica",
            "CL": {
                "label": "Lavado de Motor",
                "aliases": ["lavado motor", "limpieza motor", "compartimento motor", "motor"]
            },
            "MX": {
                "label": "Lavado de Motor",
                "aliases": ["lavado motor", "limpieza motor", "compartimento motor", "motor"]
            },
            "US": {
                "label": "Engine Bay Cleaning",
                "aliases": ["engine cleaning", "engine bay", "engine wash", "motor cleaning"]
            },
            "PE": {
                "label": "Lavado de Motor",
                "aliases": ["lavado motor", "limpieza motor", "compartimento motor"]
            },
            "VE": {
                "label": "Lavado de Motor",
                "aliases": ["lavado motor", "limpieza motor", "compartimento motor"]
            },
            "BR": {
                "label": "Limpeza de Motor",
                "aliases": ["limpeza motor", "lavagem motor", "compartimento motor"]
            }
        },
        "DIAGNOSTIC_SCAN": {
            "code": "DIAGNOSTIC_SCAN",
            "categoria": "especialidades",
            "CL": {
                "label": "Diagnóstico Computarizado",
                "aliases": ["scanner", "diagnóstico", "obd", "check engine", "códigos", "lectura códigos"]
            },
            "MX": {
                "label": "Escaneo Diagnóstico",
                "aliases": ["scanner", "diagnóstico", "obd", "check engine", "códigos", "lectura"]
            },
            "US": {
                "label": "Computerized Diagnostic Scan",
                "aliases": ["scanner", "diagnostic", "obd", "check engine", "code reading", "scan"]
            },
            "PE": {
                "label": "Diagnóstico Computarizado",
                "aliases": ["scanner", "diagnóstico", "obd", "check engine"]
            },
            "VE": {
                "label": "Diagnóstico Computarizado",
                "aliases": ["scanner", "diagnóstico", "obd", "check engine"]
            },
            "BR": {
                "label": "Varredura Diagnóstica",
                "aliases": ["scanner", "diagnóstico", "obd", "check engine", "leitura códigos"]
            }
        },
    }
    
    # Mapeo de categorías
    categorias_map = {
        "mantenimiento": {
            "CL": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo", "servicio periódico"]},
            "MX": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo", "servicio periódico"]},
            "US": {"label": "Preventive Maintenance", "aliases": ["maintenance", "preventive", "periodic service"]},
            "PE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "VE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
            "BR": {"label": "Manutenção Periódica", "aliases": ["manutenção", "preventivo"]},
        },
        "frenos": {
            "CL": {"label": "Sistema de Frenos", "aliases": ["frenos", "frenado", "pastillas"]},
            "MX": {"label": "Sistema de Frenos", "aliases": ["frenos", "frenado", "balatas", "pastillas"]},
            "US": {"label": "Braking System", "aliases": ["brakes", "braking", "pads"]},
            "PE": {"label": "Sistema de Frenos", "aliases": ["frenos", "frenado", "pastillas"]},
            "VE": {"label": "Sistema de Frenos", "aliases": ["frenos", "frenado", "pastillas"]},
            "BR": {"label": "Sistema de Freios", "aliases": ["freios", "freagem", "pastilhas"]},
        },
        "estetica": {
            "CL": {"label": "Carwash y Detailing", "aliases": ["detailing", "carwash", "lavado", "pulido"]},
            "MX": {"label": "Carwash y Detailing", "aliases": ["detailing", "carwash", "lavado", "pulido"]},
            "US": {"label": "Carwash & Detailing", "aliases": ["detailing", "carwash", "wash", "polish"]},
            "PE": {"label": "Carwash y Detailing", "aliases": ["detailing", "carwash", "lavado"]},
            "VE": {"label": "Carwash y Detailing", "aliases": ["detailing", "carwash", "lavado"]},
            "BR": {"label": "Lavagem e Detalhamento", "aliases": ["detalhamento", "lavagem", "polimento"]},
        },
        "especialidades": {
            "CL": {"label": "Servicios Especializados", "aliases": ["especializado", "servicios varios"]},
            "MX": {"label": "Servicios Especializados", "aliases": ["especializado", "servicios varios"]},
            "US": {"label": "Specialized Services", "aliases": ["specialized", "various services"]},
            "PE": {"label": "Servicios Especializados", "aliases": ["especializado"]},
            "VE": {"label": "Servicios Especializados", "aliases": ["especializado"]},
            "BR": {"label": "Serviços Especializados", "aliases": ["especializado"]},
        },
    }
    
    servicios_creados = 0
    servicios_actualizados = 0
    
    # Procesar cada servicio del catálogo
    for servicio_code, servicio_data in catalogo_regional.items():
        cat_code = servicio_data["categoria"]
        
        # Crear categorías para cada país
        categorias_por_pais = {}
        for country in ["CL", "MX", "US", "PE", "VE", "BR"]:
            if country in categorias_map.get(cat_code, {}):
                categoria, _ = CategoriaServicio.objects.get_or_create(
                    code=cat_code,
                    country=country,
                    defaults={"activo": True}
                )
                
                # Crear nombre de categoría
                cat_info = categorias_map[cat_code][country]
                lang_map = {"CL": "es", "MX": "es", "US": "en", "PE": "es", "VE": "es", "BR": "pt"}
                language = lang_map[country]
                
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
        
        # Crear servicio para cada país con sus aliases específicos
        for country in ["CL", "MX", "US", "PE", "VE", "BR"]:
            if country not in servicio_data:
                continue
            
            categoria = categorias_por_pais.get(country)
            if not categoria:
                continue
            
            servicio_info = servicio_data[country]
            label = servicio_info["label"]
            aliases = servicio_info.get("aliases", [])
            
            # Determinar idioma
            lang_map = {"CL": "es", "MX": "es", "US": "en", "PE": "es", "VE": "es", "BR": "pt"}
            language = lang_map[country]
            
            # Crear servicio
            servicio, created = Servicio.objects.get_or_create(
                nombre=label,
                empresa_id=MASTER_ID,
                categoria=categoria,
                defaults={
                    "activo": True,
                    "precio_base": Decimal("0.00")
                }
            )
            
            if created:
                servicios_creados += 1
            else:
                servicios_actualizados += 1
            
            # Crear nombre localizado con aliases regionales
            ServicioName.objects.update_or_create(
                servicio=servicio,
                language=language,
                is_default=True,
                defaults={
                    "label": label,
                    "aliases": aliases,  # Aliases específicos de la región
                }
            )
            
            print(f"   🔧 [{country}] {label} - Aliases: {', '.join(aliases[:3])}...")
    
    total = Servicio.objects.filter(empresa_id=MASTER_ID).count()
    
    return f"""
✅ Catálogo maestro regional poblado exitosamente.
📊 Resumen:
   - Servicios creados: {servicios_creados}
   - Servicios actualizados: {servicios_actualizados}
   - Total en catálogo: {total}
   - Aliases regionales configurados para: CL, MX, US, PE, VE, BR
   
🎯 Ejemplos de búsqueda regional:
   - MX: "afinación" → encontrará "Servicio de Aceite"
   - CL: "mantención" → encontrará "Cambio de Aceite y Filtro"
   - US: "lube" → encontrará "Oil Change"
   - MX: "llantera" → encontrará servicios de neumáticos
   - CL: "vulcanización" → encontrará servicios de neumáticos
"""


if __name__ == "__main__":
    print("="*60)
    print("🌍 POBLANDO CATÁLOGO MAESTRO CON ALIASES REGIONALES")
    print("="*60)
    resultado = poblar_catalogo_regional()
    print(resultado)
    print("="*60)






