#!/usr/bin/env python3
"""
Script de Seed para Catálogo Maestro Universal de Servicios

Este script crea un catálogo maestro completo de servicios organizados por "Sistemas"
en lugar de "Rubros", excluyendo desarmadurías.

Estructura:
- 9 categorías principales (sistemas)
- ~200 servicios maestros con aliases para búsqueda inteligente
- Soporte multi-idioma (es, en, pt)
- Servicios globales (empresa_id=1)

Uso:
    python manage.py shell < scripts/seed_catalogo_maestro_servicios.py
    O ejecutar directamente: python scripts/seed_catalogo_maestro_servicios.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.empresa import Empresa
from taller.servicios.models import (
    CategoriaServicio,
    CategoriaServicioName,
    Servicio,
    ServicioName,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)

# ============================================================================
# CONFIGURACIÓN DE CATEGORÍAS Y SERVICIOS
# ============================================================================

CATEGORIAS_SISTEMAS = {
    "MAINTENANCE": {
        "code": "MAINTENANCE",
        "orden": 1,
        "names": {
            "es": {
                "label": "Mantenimiento Periódico",
                "aliases": ["mantenimiento", "preventivo", "servicio periódico"],
            },
            "en": {
                "label": "Periodic Maintenance",
                "aliases": ["maintenance", "preventive", "periodic service"],
            },
            "pt": {
                "label": "Manutenção Periódica",
                "aliases": ["manutenção", "preventivo", "serviço periódico"],
            },
        },
        "subcategorias": {
            "OIL_CHANGE": {
                "code": "OIL_CHANGE",
                "orden": 1,
                "names": {
                    "es": {
                        "label": "Cambio de Aceite y Filtros",
                        "aliases": ["aceite", "filtro", "lubricante"],
                    },
                    "en": {
                        "label": "Oil Change and Filters",
                        "aliases": ["oil", "filter", "lubricant"],
                    },
                    "pt": {
                        "label": "Troca de Óleo e Filtros",
                        "aliases": ["óleo", "filtro", "lubricante"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de aceite y filtro",
                                "aliases": ["aceite", "filtro aceite", "cambio aceite"],
                            },
                            "en": {
                                "label": "Oil change and filter",
                                "aliases": ["oil change", "oil filter", "lube"],
                            },
                            "pt": {
                                "label": "Troca de óleo e filtro",
                                "aliases": ["troca óleo", "filtro óleo", "óleo"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de filtro de aire",
                                "aliases": ["filtro aire", "filtro motor"],
                            },
                            "en": {
                                "label": "Air filter replacement",
                                "aliases": ["air filter", "engine filter"],
                            },
                            "pt": {
                                "label": "Troca de filtro de ar",
                                "aliases": ["filtro ar", "filtro motor"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de filtro de cabina",
                                "aliases": ["filtro habitáculo", "filtro polen"],
                            },
                            "en": {
                                "label": "Cabin filter replacement",
                                "aliases": ["cabin filter", "pollen filter"],
                            },
                            "pt": {
                                "label": "Troca de filtro de cabine",
                                "aliases": ["filtro cabine", "filtro pólen"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de filtro de combustible",
                                "aliases": ["filtro gasolina", "filtro diesel"],
                            },
                            "en": {
                                "label": "Fuel filter replacement",
                                "aliases": ["fuel filter", "gas filter"],
                            },
                            "pt": {
                                "label": "Troca de filtro de combustível",
                                "aliases": ["filtro combustível", "filtro gasolina"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de aceite sintético",
                                "aliases": ["aceite sintético", "sintético", "full synthetic"],
                            },
                            "en": {
                                "label": "Synthetic oil change",
                                "aliases": ["synthetic oil", "full synthetic", "synthetic"],
                            },
                            "pt": {
                                "label": "Troca de óleo sintético",
                                "aliases": ["óleo sintético", "sintético"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de aceite semi-sintético",
                                "aliases": ["aceite semi", "blend", "semi sintético"],
                            },
                            "en": {
                                "label": "Synthetic blend oil change",
                                "aliases": ["blend", "semi synthetic", "synthetic blend"],
                            },
                            "pt": {
                                "label": "Troca de óleo semi-sintético",
                                "aliases": ["óleo semi", "blend", "semi sintético"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de plumillas",
                                "aliases": ["plumillas", "limpiaparabrisas", "wiper blades"],
                            },
                            "en": {
                                "label": "Wiper blades replacement",
                                "aliases": ["wiper blades", "windshield wipers", "wipers"],
                            },
                            "pt": {
                                "label": "Troca de palhetas",
                                "aliases": ["palhetas", "limpadores", "wiper blades"],
                            },
                        }
                    },
                ],
            },
            "PERIODIC_SERVICE": {
                "code": "PERIODIC_SERVICE",
                "orden": 2,
                "names": {
                    "es": {
                        "label": "Revisión Periódica",
                        "aliases": ["revisión", "inspección", "chequeo"],
                    },
                    "en": {
                        "label": "Periodic Inspection",
                        "aliases": ["inspection", "check", "service"],
                    },
                    "pt": {
                        "label": "Inspeção Periódica",
                        "aliases": ["inspeção", "revisão", "verificação"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Revisión de 10,000 km",
                                "aliases": ["10k", "10 mil", "revisión 10"],
                            },
                            "en": {
                                "label": "10,000 mile service",
                                "aliases": ["10k", "10k service"],
                            },
                            "pt": {"label": "Revisão de 10.000 km", "aliases": ["10k", "10 mil"]},
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Revisión de 20,000 km",
                                "aliases": ["20k", "20 mil", "revisión 20"],
                            },
                            "en": {
                                "label": "20,000 mile service",
                                "aliases": ["20k", "20k service"],
                            },
                            "pt": {"label": "Revisão de 20.000 km", "aliases": ["20k", "20 mil"]},
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Rotación de neumáticos",
                                "aliases": ["rotación", "cambio posición llantas"],
                            },
                            "en": {
                                "label": "Tire rotation",
                                "aliases": ["rotation", "tire rotation"],
                            },
                            "pt": {
                                "label": "Rotação de pneus",
                                "aliases": ["rotação", "troca posição pneus"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Revisión de niveles de fluidos",
                                "aliases": ["niveles", "líquidos", "fluidos"],
                            },
                            "en": {
                                "label": "Fluid level check",
                                "aliases": ["fluids", "levels", "fluid check"],
                            },
                            "pt": {
                                "label": "Verificação de níveis de fluidos",
                                "aliases": ["níveis", "líquidos", "fluidos"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Revisión de 30,000 km",
                                "aliases": ["30k", "30 mil", "revisión 30"],
                            },
                            "en": {
                                "label": "30,000 mile service",
                                "aliases": ["30k", "30k service"],
                            },
                            "pt": {"label": "Revisão de 30.000 km", "aliases": ["30k", "30 mil"]},
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Revisión de 50,000 km",
                                "aliases": ["50k", "50 mil", "revisión 50"],
                            },
                            "en": {
                                "label": "50,000 mile service",
                                "aliases": ["50k", "50k service"],
                            },
                            "pt": {"label": "Revisão de 50.000 km", "aliases": ["50k", "50 mil"]},
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Fluid top-off",
                                "aliases": ["completar fluidos", "rellenar líquidos", "top off"],
                            },
                            "en": {
                                "label": "Fluid top-off",
                                "aliases": ["top off", "fluid top", "refill fluids"],
                            },
                            "pt": {
                                "label": "Completar fluidos",
                                "aliases": ["completar", "reabastecer fluidos"],
                            },
                        }
                    },
                ],
            },
        },
    },
    "BRAKES": {
        "code": "BRAKES",
        "orden": 2,
        "names": {
            "es": {"label": "Sistema de Frenos", "aliases": ["frenos", "frenado", "pastillas"]},
            "en": {"label": "Brake System", "aliases": ["brakes", "braking", "pads"]},
            "pt": {"label": "Sistema de Freios", "aliases": ["freios", "freagem", "pastilhas"]},
        },
        "subcategorias": {
            "BRAKE_PADS": {
                "code": "BRAKE_PADS",
                "orden": 1,
                "names": {
                    "es": {
                        "label": "Pastillas y Discos",
                        "aliases": ["pastillas", "discos", "frenos delanteros"],
                    },
                    "en": {
                        "label": "Pads and Rotors",
                        "aliases": ["pads", "rotors", "front brakes"],
                    },
                    "pt": {
                        "label": "Pastilhas e Discos",
                        "aliases": ["pastilhas", "discos", "freios dianteiros"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de pastillas de freno delanteras",
                                "aliases": [
                                    "pastillas delanteras",
                                    "frenos delanteros",
                                    "front pads",
                                ],
                            },
                            "en": {
                                "label": "Front brake pad replacement",
                                "aliases": ["front pads", "front brakes", "front brake pads"],
                            },
                            "pt": {
                                "label": "Troca de pastilhas dianteiras",
                                "aliases": ["pastilhas dianteiras", "freios dianteiros"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de pastillas de freno traseras",
                                "aliases": ["pastillas traseras", "frenos traseros", "rear pads"],
                            },
                            "en": {
                                "label": "Rear brake pad replacement",
                                "aliases": ["rear pads", "rear brakes", "rear brake pads"],
                            },
                            "pt": {
                                "label": "Troca de pastilhas traseiras",
                                "aliases": ["pastilhas traseiras", "freios traseiros"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de pastillas de freno (completo)",
                                "aliases": ["pastillas", "frenos", "pastillas completo"],
                            },
                            "en": {
                                "label": "Brake pad replacement (full)",
                                "aliases": ["brake pads", "pads", "full brake pads"],
                            },
                            "pt": {
                                "label": "Troca de pastilhas completo",
                                "aliases": ["pastilhas", "freios", "pastilhas completo"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Rectificado de discos",
                                "aliases": ["rectificar discos", "machacar discos", "disco freno"],
                            },
                            "en": {
                                "label": "Rotor resurfacing",
                                "aliases": ["resurface rotors", "turn rotors", "brake rotors"],
                            },
                            "pt": {
                                "label": "Retificação de discos",
                                "aliases": ["retificar discos", "discos freio"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de discos de freno",
                                "aliases": ["discos", "discos nuevos", "reemplazo discos"],
                            },
                            "en": {
                                "label": "Brake rotor replacement",
                                "aliases": ["rotors", "new rotors", "rotor replacement"],
                            },
                            "pt": {
                                "label": "Troca de discos de freio",
                                "aliases": ["discos", "discos novos", "substituição discos"],
                            },
                        }
                    },
                ],
            },
            "BRAKE_FLUID": {
                "code": "BRAKE_FLUID",
                "orden": 2,
                "names": {
                    "es": {
                        "label": "Líquido de Frenos",
                        "aliases": ["líquido frenos", "sangrado", "purga"],
                    },
                    "en": {"label": "Brake Fluid", "aliases": ["brake fluid", "bleeding", "flush"]},
                    "pt": {
                        "label": "Fluido de Freios",
                        "aliases": ["fluido freios", "sangria", "purga"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de líquido de frenos",
                                "aliases": ["líquido frenos", "purga frenos", "sangrado"],
                            },
                            "en": {
                                "label": "Brake fluid flush",
                                "aliases": ["brake fluid", "bleed brakes", "brake flush"],
                            },
                            "pt": {
                                "label": "Troca de fluido de freios",
                                "aliases": ["fluido freios", "purga freios", "sangria"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Diagnóstico de ABS",
                                "aliases": ["abs", "antibloqueo", "sistema abs"],
                            },
                            "en": {
                                "label": "ABS diagnosis",
                                "aliases": ["abs", "antilock", "abs system"],
                            },
                            "pt": {
                                "label": "Diagnóstico de ABS",
                                "aliases": ["abs", "antitravamento", "sistema abs"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de cilindro maestro de frenos",
                                "aliases": ["cilindro maestro", "master cylinder", "bomba frenos"],
                            },
                            "en": {
                                "label": "Master cylinder replacement",
                                "aliases": ["master cylinder", "brake master", "brake cylinder"],
                            },
                            "pt": {
                                "label": "Troca de cilindro mestre",
                                "aliases": ["cilindro mestre", "master cylinder"],
                            },
                        }
                    },
                ],
            },
        },
    },
    "SUSPENSION": {
        "code": "SUSPENSION",
        "orden": 3,
        "names": {
            "es": {
                "label": "Tren Delantero y Suspensión",
                "aliases": ["suspensión", "alineación", "amortiguadores"],
            },
            "en": {
                "label": "Front End and Suspension",
                "aliases": ["suspension", "alignment", "shocks"],
            },
            "pt": {
                "label": "Suspensão e Direção",
                "aliases": ["suspensão", "alinhamento", "amortecedores"],
            },
        },
        "subcategorias": {
            "ALIGNMENT": {
                "code": "ALIGNMENT",
                "orden": 1,
                "names": {
                    "es": {
                        "label": "Alineación y Balanceo",
                        "aliases": ["alineación", "balanceo", "geometría"],
                    },
                    "en": {
                        "label": "Alignment and Balancing",
                        "aliases": ["alignment", "balancing", "geometry"],
                    },
                    "pt": {
                        "label": "Alinhamento e Balanceamento",
                        "aliases": ["alinhamento", "balanceamento", "geometria"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Alineación y balanceo",
                                "aliases": ["alineación", "balanceo", "alinear", "balancear"],
                            },
                            "en": {
                                "label": "Wheel alignment and balancing",
                                "aliases": ["alignment", "balancing", "align", "balance"],
                            },
                            "pt": {
                                "label": "Alinhamento e balanceamento",
                                "aliases": ["alinhamento", "balanceamento", "alinhar", "balancear"],
                            },
                        }
                    },
                ],
            },
            "SHOCKS": {
                "code": "SHOCKS",
                "orden": 2,
                "names": {
                    "es": {
                        "label": "Amortiguadores y Componentes",
                        "aliases": ["amortiguadores", "suspensión", "shocks"],
                    },
                    "en": {
                        "label": "Shocks and Components",
                        "aliases": ["shocks", "struts", "suspension"],
                    },
                    "pt": {
                        "label": "Amortecedores e Componentes",
                        "aliases": ["amortecedores", "suspensão", "shocks"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de amortiguadores",
                                "aliases": ["amortiguadores", "shocks", "suspensión"],
                            },
                            "en": {
                                "label": "Shock absorber replacement",
                                "aliases": ["shocks", "struts", "suspension"],
                            },
                            "pt": {
                                "label": "Troca de amortecedores",
                                "aliases": ["amortecedores", "shocks", "suspensão"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de bujes de suspensión",
                                "aliases": ["bujes", "bushings", "suspensión"],
                            },
                            "en": {
                                "label": "Suspension bushing replacement",
                                "aliases": ["bushings", "suspension"],
                            },
                            "pt": {
                                "label": "Troca de buchas de suspensão",
                                "aliases": ["buchas", "suspensão"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de terminales de dirección",
                                "aliases": ["terminales", "dirección", "tie rods"],
                            },
                            "en": {
                                "label": "Tie rod replacement",
                                "aliases": ["tie rods", "steering", "ends"],
                            },
                            "pt": {
                                "label": "Troca de terminais de direção",
                                "aliases": ["terminais", "direção"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de brazos de control",
                                "aliases": ["brazos control", "control arms", "suspensión"],
                            },
                            "en": {
                                "label": "Control arm replacement",
                                "aliases": ["control arms", "suspension arms", "control"],
                            },
                            "pt": {
                                "label": "Troca de braços de controle",
                                "aliases": ["braços controle", "suspensão"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de bomba de dirección asistida",
                                "aliases": [
                                    "bomba dirección",
                                    "power steering",
                                    "dirección hidráulica",
                                ],
                            },
                            "en": {
                                "label": "Power steering pump replacement",
                                "aliases": ["power steering", "steering pump", "ps pump"],
                            },
                            "pt": {
                                "label": "Troca de bomba de direção hidráulica",
                                "aliases": ["bomba direção", "direção hidráulica"],
                            },
                        }
                    },
                ],
            },
        },
    },
    "ENGINE": {
        "code": "ENGINE",
        "orden": 4,
        "names": {
            "es": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
            "en": {
                "label": "Engine and Transmission",
                "aliases": ["engine", "transmission", "gearbox"],
            },
            "pt": {"label": "Motor e Transmissão", "aliases": ["motor", "transmissão", "câmbio"]},
        },
        "subcategorias": {
            "ENGINE_REPAIR": {
                "code": "ENGINE_REPAIR",
                "orden": 1,
                "names": {
                    "es": {
                        "label": "Reparación de Motor",
                        "aliases": ["motor", "reparación motor", "mecánica"],
                    },
                    "en": {
                        "label": "Engine Repair",
                        "aliases": ["engine", "engine repair", "mechanical"],
                    },
                    "pt": {
                        "label": "Reparo de Motor",
                        "aliases": ["motor", "reparo motor", "mecânica"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de culata",
                                "aliases": ["culata", "junta culata", "rectificar culata"],
                            },
                            "en": {
                                "label": "Cylinder head repair",
                                "aliases": ["head", "head gasket", "head repair"],
                            },
                            "pt": {
                                "label": "Reparo de cabeçote",
                                "aliases": ["cabeçote", "junta cabeçote", "retificar cabeçote"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de kit de distribución",
                                "aliases": ["distribución", "timing belt", "correa distribución"],
                            },
                            "en": {
                                "label": "Timing belt replacement",
                                "aliases": ["timing belt", "timing chain", "belt"],
                            },
                            "pt": {
                                "label": "Troca de kit de distribuição",
                                "aliases": ["distribuição", "correia distribuição", "timing belt"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Sellado de fugas de aceite",
                                "aliases": ["fuga aceite", "goteo", "retenes"],
                            },
                            "en": {
                                "label": "Oil leak repair",
                                "aliases": ["oil leak", "seal", "gaskets"],
                            },
                            "pt": {
                                "label": "Vedação de vazamentos de óleo",
                                "aliases": ["vazamento óleo", "gotejamento", "retentores"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de bomba de agua",
                                "aliases": ["bomba agua", "water pump", "bomba refrigerante"],
                            },
                            "en": {
                                "label": "Water pump replacement",
                                "aliases": ["water pump", "coolant pump", "pump"],
                            },
                            "pt": {
                                "label": "Troca de bomba d'água",
                                "aliases": ["bomba água", "bomba refrigerante"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de bujías",
                                "aliases": ["bujías", "spark plugs", "chisperos"],
                            },
                            "en": {
                                "label": "Spark plug replacement",
                                "aliases": ["spark plugs", "plugs", "ignition"],
                            },
                            "pt": {
                                "label": "Troca de velas",
                                "aliases": ["velas", "spark plugs", "ignição"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Limpieza de inyectores",
                                "aliases": ["inyectores", "fuel injectors", "limpieza inyectores"],
                            },
                            "en": {
                                "label": "Fuel injector cleaning",
                                "aliases": ["injector cleaning", "fuel injectors", "injectors"],
                            },
                            "pt": {
                                "label": "Limpeza de injetores",
                                "aliases": ["injetores", "limpeza injetores"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de junta de tapa de válvulas",
                                "aliases": [
                                    "junta válvulas",
                                    "valve cover gasket",
                                    "tapa válvulas",
                                ],
                            },
                            "en": {
                                "label": "Valve cover gasket replacement",
                                "aliases": ["valve cover", "gasket", "valve cover gasket"],
                            },
                            "pt": {
                                "label": "Troca de junta de tampa de válvulas",
                                "aliases": ["junta válvulas", "tampa válvulas"],
                            },
                        }
                    },
                ],
            },
            "TRANSMISSION": {
                "code": "TRANSMISSION",
                "orden": 2,
                "names": {
                    "es": {"label": "Transmisión", "aliases": ["transmisión", "caja", "embrague"]},
                    "en": {
                        "label": "Transmission",
                        "aliases": ["transmission", "gearbox", "clutch"],
                    },
                    "pt": {
                        "label": "Transmissão",
                        "aliases": ["transmissão", "câmbio", "embreagem"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de embrague",
                                "aliases": ["embrague", "clutch", "kit embrague"],
                            },
                            "en": {
                                "label": "Clutch replacement",
                                "aliases": ["clutch", "clutch kit"],
                            },
                            "pt": {
                                "label": "Troca de embreagem",
                                "aliases": ["embreagem", "kit embreagem"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de caja automática",
                                "aliases": ["caja automática", "transmisión automática", "atf"],
                            },
                            "en": {
                                "label": "Automatic transmission repair",
                                "aliases": ["automatic", "transmission", "atf"],
                            },
                            "pt": {
                                "label": "Reparo de câmbio automático",
                                "aliases": ["câmbio automático", "transmissão automática"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de caja manual",
                                "aliases": ["caja manual", "transmisión manual"],
                            },
                            "en": {
                                "label": "Manual transmission repair",
                                "aliases": ["manual", "gearbox", "transmission"],
                            },
                            "pt": {
                                "label": "Reparo de câmbio manual",
                                "aliases": ["câmbio manual", "transmissão manual"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Servicio de fluido de transmisión",
                                "aliases": ["transmisión", "atf", "fluido caja"],
                            },
                            "en": {
                                "label": "Transmission fluid service",
                                "aliases": ["transmission", "atf", "transmission service"],
                            },
                            "pt": {
                                "label": "Serviço de fluido de transmissão",
                                "aliases": ["transmissão", "atf", "fluido câmbio"],
                            },
                        }
                    },
                ],
            },
        },
    },
    "ELECTRICAL": {
        "code": "ELECTRICAL",
        "orden": 5,
        "names": {
            "es": {
                "label": "Electricidad y Electrónica",
                "aliases": ["eléctrico", "electrónica", "batería"],
            },
            "en": {
                "label": "Electrical and Electronics",
                "aliases": ["electrical", "electronics", "battery"],
            },
            "pt": {
                "label": "Elétrica e Eletrônica",
                "aliases": ["elétrica", "eletrônica", "bateria"],
            },
        },
        "subcategorias": {
            "DIAGNOSTIC": {
                "code": "DIAGNOSTIC",
                "orden": 1,
                "names": {
                    "es": {"label": "Diagnóstico", "aliases": ["diagnóstico", "scanner", "obd"]},
                    "en": {"label": "Diagnostics", "aliases": ["diagnostic", "scanner", "obd"]},
                    "pt": {"label": "Diagnóstico", "aliases": ["diagnóstico", "scanner", "obd"]},
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Diagnóstico con scanner",
                                "aliases": ["scanner", "obd", "diagnóstico computarizado"],
                            },
                            "en": {
                                "label": "Scanner diagnosis",
                                "aliases": ["scanner", "obd", "computer diagnosis"],
                            },
                            "pt": {
                                "label": "Diagnóstico com scanner",
                                "aliases": ["scanner", "obd", "diagnóstico computadorizado"],
                            },
                        }
                    },
                ],
            },
            "BATTERY": {
                "code": "BATTERY",
                "orden": 2,
                "names": {
                    "es": {
                        "label": "Batería y Carga",
                        "aliases": ["batería", "alternador", "arranque"],
                    },
                    "en": {
                        "label": "Battery and Charging",
                        "aliases": ["battery", "alternator", "starter"],
                    },
                    "pt": {
                        "label": "Bateria e Carga",
                        "aliases": ["bateria", "alternador", "partida"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de batería",
                                "aliases": ["batería", "batería nueva", "instalación batería"],
                            },
                            "en": {
                                "label": "Battery replacement",
                                "aliases": ["battery", "new battery", "battery install"],
                            },
                            "pt": {
                                "label": "Troca de bateria",
                                "aliases": ["bateria", "bateria nova", "instalação bateria"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de alternador",
                                "aliases": ["alternador", "generador", "carga"],
                            },
                            "en": {
                                "label": "Alternator repair",
                                "aliases": ["alternator", "generator", "charging"],
                            },
                            "pt": {
                                "label": "Reparo de alternador",
                                "aliases": ["alternador", "gerador", "carga"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de motor de arranque",
                                "aliases": ["arranque", "starter", "motor partida"],
                            },
                            "en": {
                                "label": "Starter motor repair",
                                "aliases": ["starter", "starting motor"],
                            },
                            "pt": {
                                "label": "Reparo de motor de partida",
                                "aliases": ["partida", "motor partida"],
                            },
                        }
                    },
                ],
            },
            "LIGHTS": {
                "code": "LIGHTS",
                "orden": 3,
                "names": {
                    "es": {"label": "Luces y Sensores", "aliases": ["luces", "focos", "sensores"]},
                    "en": {
                        "label": "Lights and Sensors",
                        "aliases": ["lights", "bulbs", "sensors"],
                    },
                    "pt": {
                        "label": "Luzes e Sensores",
                        "aliases": ["luzes", "lâmpadas", "sensores"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de focos y luces",
                                "aliases": ["focos", "luces", "ampolletas", "led"],
                            },
                            "en": {
                                "label": "Light bulb replacement",
                                "aliases": ["lights", "bulbs", "led"],
                            },
                            "pt": {
                                "label": "Troca de lâmpadas e luzes",
                                "aliases": ["lâmpadas", "luzes", "led"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Programación de llaves",
                                "aliases": ["llaves", "programar llave", "llave programada"],
                            },
                            "en": {
                                "label": "Key programming",
                                "aliases": ["keys", "program key", "key fob"],
                            },
                            "pt": {
                                "label": "Programação de chaves",
                                "aliases": ["chaves", "programar chave", "chave programada"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Diagnóstico computarizado OBDII",
                                "aliases": ["obd", "obd2", "scanner", "diagnóstico"],
                            },
                            "en": {
                                "label": "Computer diagnostics (OBDII)",
                                "aliases": ["obd", "obd2", "scanner", "diagnostic"],
                            },
                            "pt": {
                                "label": "Diagnóstico computadorizado OBDII",
                                "aliases": ["obd", "obd2", "scanner", "diagnóstico"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de fusibles",
                                "aliases": ["fusibles", "fuses", "caja fusibles"],
                            },
                            "en": {
                                "label": "Fuse replacement",
                                "aliases": ["fuses", "fuse box", "fuse"],
                            },
                            "pt": {
                                "label": "Troca de fusíveis",
                                "aliases": ["fusíveis", "fuses", "caixa fusíveis"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de cableado eléctrico",
                                "aliases": ["cableado", "wiring", "ramal eléctrico"],
                            },
                            "en": {
                                "label": "Wiring repair",
                                "aliases": ["wiring", "electrical", "wire repair"],
                            },
                            "pt": {
                                "label": "Reparo de fiação elétrica",
                                "aliases": ["fiação", "wiring", "ramal elétrico"],
                            },
                        }
                    },
                ],
            },
        },
    },
    "AC": {
        "code": "AC",
        "orden": 6,
        "names": {
            "es": {
                "label": "Climatización (A/C)",
                "aliases": ["aire acondicionado", "ac", "clima", "refrigeración"],
            },
            "en": {
                "label": "Air Conditioning",
                "aliases": ["ac", "air conditioning", "climate", "cooling"],
            },
            "pt": {
                "label": "Climatização (Ar Condicionado)",
                "aliases": ["ar condicionado", "ac", "clima", "refrigeração"],
            },
        },
        "subcategorias": {
            "AC_SERVICE": {
                "code": "AC_SERVICE",
                "orden": 1,
                "names": {
                    "es": {"label": "Servicio de A/C", "aliases": ["aire", "ac", "refrigerante"]},
                    "en": {"label": "AC Service", "aliases": ["ac", "air", "refrigerant"]},
                    "pt": {
                        "label": "Serviço de Ar Condicionado",
                        "aliases": ["ar", "ac", "refrigerante"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Carga de gas refrigerante",
                                "aliases": ["gas", "refrigerante", "r134a", "recarga"],
                            },
                            "en": {
                                "label": "Refrigerant recharge",
                                "aliases": ["refrigerant", "gas", "r134a", "recharge"],
                            },
                            "pt": {
                                "label": "Carga de gás refrigerante",
                                "aliases": ["gás", "refrigerante", "r134a", "recarga"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Detección de fugas de A/C",
                                "aliases": ["fuga ac", "fuga aire", "detección fugas"],
                            },
                            "en": {
                                "label": "AC leak detection",
                                "aliases": ["ac leak", "air leak", "leak detection"],
                            },
                            "pt": {
                                "label": "Detecção de vazamentos de ar",
                                "aliases": ["vazamento ar", "vazamento ac", "detecção vazamentos"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Reemplazo de compresor de A/C",
                                "aliases": ["compresor", "compresor ac", "compresor aire"],
                            },
                            "en": {
                                "label": "AC compressor replacement",
                                "aliases": ["compressor", "ac compressor"],
                            },
                            "pt": {
                                "label": "Substituição de compressor de ar",
                                "aliases": ["compressor", "compressor ar"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Limpieza de ductos de A/C",
                                "aliases": ["limpieza ductos", "limpieza aire", "ductos"],
                            },
                            "en": {
                                "label": "AC duct cleaning",
                                "aliases": ["duct cleaning", "air cleaning", "ducts"],
                            },
                            "pt": {
                                "label": "Limpeza de dutos de ar",
                                "aliases": ["limpeza dutos", "limpeza ar", "dutos"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Carga de gas R134a",
                                "aliases": ["r134a", "gas r134a", "recarga r134a"],
                            },
                            "en": {
                                "label": "R134a recharge",
                                "aliases": ["r134a", "r134a gas", "r134a recharge"],
                            },
                            "pt": {
                                "label": "Carga de gás R134a",
                                "aliases": ["r134a", "gás r134a", "recarga r134a"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Carga de gas R1234yf",
                                "aliases": ["r1234yf", "gas r1234yf", "recarga r1234yf"],
                            },
                            "en": {
                                "label": "R1234yf recharge",
                                "aliases": ["r1234yf", "r1234yf gas", "r1234yf recharge"],
                            },
                            "pt": {
                                "label": "Carga de gás R1234yf",
                                "aliases": ["r1234yf", "gás r1234yf", "recarga r1234yf"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Limpieza de evaporador",
                                "aliases": ["evaporador", "limpieza evaporador", "ac evaporator"],
                            },
                            "en": {
                                "label": "Evaporator cleaning",
                                "aliases": ["evaporator", "evaporator clean", "ac evaporator"],
                            },
                            "pt": {
                                "label": "Limpeza de evaporador",
                                "aliases": ["evaporador", "limpeza evaporador"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Limpieza de núcleo de calefacción",
                                "aliases": ["heater core", "núcleo calefacción", "calefacción"],
                            },
                            "en": {
                                "label": "Heater core flush",
                                "aliases": ["heater core", "heater", "core flush"],
                            },
                            "pt": {
                                "label": "Limpeza de núcleo de aquecimento",
                                "aliases": ["núcleo aquecimento", "aquecimento"],
                            },
                        }
                    },
                ],
            },
        },
    },
    "DETAILING": {
        "code": "DETAILING",
        "orden": 7,
        "names": {
            "es": {
                "label": "Estética Automotriz",
                "aliases": ["detailing", "carwash", "lavado", "pulido"],
            },
            "en": {
                "label": "Auto Detailing",
                "aliases": ["detailing", "carwash", "wash", "polish"],
            },
            "pt": {
                "label": "Estética Automotiva",
                "aliases": ["detalhamento", "lavagem", "polimento"],
            },
        },
        "subcategorias": {
            "CARWASH": {
                "code": "CARWASH",
                "orden": 1,
                "names": {
                    "es": {
                        "label": "Lavado y Limpieza",
                        "aliases": ["lavado", "carwash", "limpieza"],
                    },
                    "en": {
                        "label": "Wash and Cleaning",
                        "aliases": ["wash", "carwash", "cleaning"],
                    },
                    "pt": {"label": "Lavagem e Limpeza", "aliases": ["lavagem", "limpeza"]},
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Lavado simple",
                                "aliases": ["lavado", "carwash", "lavado básico"],
                            },
                            "en": {
                                "label": "Basic car wash",
                                "aliases": ["wash", "carwash", "basic wash"],
                            },
                            "pt": {
                                "label": "Lavagem simples",
                                "aliases": ["lavagem", "lavagem básica"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Lavado de motor",
                                "aliases": [
                                    "motor",
                                    "limpieza motor",
                                    "lavado compartimento motor",
                                ],
                            },
                            "en": {
                                "label": "Engine bay cleaning",
                                "aliases": ["engine", "engine cleaning", "engine bay"],
                            },
                            "pt": {
                                "label": "Limpeza de motor",
                                "aliases": ["motor", "limpeza motor", "compartimento motor"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Limpieza de tapiz",
                                "aliases": ["tapiz", "aspirado", "interior"],
                            },
                            "en": {
                                "label": "Interior cleaning",
                                "aliases": ["interior", "vacuum", "upholstery"],
                            },
                            "pt": {
                                "label": "Limpeza de estofados",
                                "aliases": ["estofados", "aspiração", "interior"],
                            },
                        }
                    },
                ],
            },
            "POLISH": {
                "code": "POLISH",
                "orden": 2,
                "names": {
                    "es": {
                        "label": "Pulido y Protección",
                        "aliases": ["pulido", "encerado", "cerámico"],
                    },
                    "en": {
                        "label": "Polish and Protection",
                        "aliases": ["polish", "wax", "ceramic"],
                    },
                    "pt": {
                        "label": "Polimento e Proteção",
                        "aliases": ["polimento", "enceramento", "cerâmico"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Pulido de carrocería",
                                "aliases": ["pulido", "pulir", "abrillantar"],
                            },
                            "en": {"label": "Body polish", "aliases": ["polish", "buff", "shine"]},
                            "pt": {
                                "label": "Polimento de carroceria",
                                "aliases": ["polimento", "polir", "brilhar"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Sellado cerámico",
                                "aliases": ["cerámico", "coating", "protección cerámica"],
                            },
                            "en": {
                                "label": "Ceramic coating",
                                "aliases": ["ceramic", "coating", "ceramic protection"],
                            },
                            "pt": {
                                "label": "Revestimento cerâmico",
                                "aliases": ["cerâmico", "coating", "proteção cerâmica"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Limpieza profunda de interior",
                                "aliases": ["interior profundo", "deep clean", "limpieza completa"],
                            },
                            "en": {
                                "label": "Interior deep clean",
                                "aliases": ["deep clean", "interior detail", "full interior"],
                            },
                            "pt": {
                                "label": "Limpeza profunda de interior",
                                "aliases": ["interior profundo", "deep clean", "limpeza completa"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Lavado exterior a mano",
                                "aliases": ["lavado mano", "hand wash", "lavado detallado"],
                            },
                            "en": {
                                "label": "Exterior hand wash",
                                "aliases": ["hand wash", "exterior detail", "hand detail"],
                            },
                            "pt": {
                                "label": "Lavagem externa manual",
                                "aliases": ["lavagem manual", "hand wash", "lavagem detalhada"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Aplicación de cera",
                                "aliases": ["cera", "wax", "encerado", "abrillantado"],
                            },
                            "en": {
                                "label": "Wax application",
                                "aliases": ["wax", "waxing", "polish wax"],
                            },
                            "pt": {
                                "label": "Aplicação de cera",
                                "aliases": ["cera", "wax", "enceramento"],
                            },
                        }
                    },
                ],
            },
        },
    },
    "BODYSHOP": {
        "code": "BODYSHOP",
        "orden": 8,
        "names": {
            "es": {
                "label": "Desabolladura y Pintura",
                "aliases": ["pintura", "desabollado", "bodyshop", "chapa"],
            },
            "en": {
                "label": "Bodywork and Paint",
                "aliases": ["paint", "bodywork", "bodyshop", "collision"],
            },
            "pt": {
                "label": "Funilaria e Pintura",
                "aliases": ["pintura", "funilaria", "bodyshop", "chapa"],
            },
        },
        "subcategorias": {
            "BODY_REPAIR": {
                "code": "BODY_REPAIR",
                "orden": 1,
                "names": {
                    "es": {
                        "label": "Desabolladura",
                        "aliases": ["desabollado", "chapa", "abolladuras"],
                    },
                    "en": {"label": "Dent Removal", "aliases": ["dent", "bodywork", "dents"]},
                    "pt": {"label": "Funilaria", "aliases": ["funilaria", "chapa", "amassados"]},
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de abolladuras",
                                "aliases": ["abolladuras", "desabollado", "chapa"],
                            },
                            "en": {
                                "label": "Dent repair",
                                "aliases": ["dents", "dent removal", "bodywork"],
                            },
                            "pt": {
                                "label": "Reparo de amassados",
                                "aliases": ["amassados", "funilaria", "chapa"],
                            },
                        }
                    },
                ],
            },
            "PAINT": {
                "code": "PAINT",
                "orden": 2,
                "names": {
                    "es": {"label": "Pintura", "aliases": ["pintura", "pintar", "barnizado"]},
                    "en": {"label": "Paint", "aliases": ["paint", "painting", "clearcoat"]},
                    "pt": {"label": "Pintura", "aliases": ["pintura", "pintar", "verniz"]},
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Pintura por pieza",
                                "aliases": ["pintura", "pintar pieza", "pintura parcial"],
                            },
                            "en": {
                                "label": "Panel painting",
                                "aliases": ["paint", "panel paint", "partial paint"],
                            },
                            "pt": {
                                "label": "Pintura por peça",
                                "aliases": ["pintura", "pintar peça", "pintura parcial"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cuadratura de chasis",
                                "aliases": ["chasis", "cuadratura", "alineación chasis"],
                            },
                            "en": {
                                "label": "Frame straightening",
                                "aliases": ["frame", "straightening", "alignment"],
                            },
                            "pt": {
                                "label": "Alinhamento de chassi",
                                "aliases": ["chassi", "alinhamento", "retificação chassi"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Restauración de parachoques",
                                "aliases": ["parachoques", "bumper", "restauración bumper"],
                            },
                            "en": {
                                "label": "Bumper restoration",
                                "aliases": ["bumper", "bumper repair", "bumper restore"],
                            },
                            "pt": {
                                "label": "Restauração de para-choques",
                                "aliases": ["para-choques", "bumper", "restauração"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Restauración de faros",
                                "aliases": [
                                    "faros",
                                    "headlights",
                                    "restauración faros",
                                    "pulido faros",
                                ],
                            },
                            "en": {
                                "label": "Headlight restoration",
                                "aliases": ["headlights", "headlight restore", "headlight polish"],
                            },
                            "pt": {
                                "label": "Restauração de faróis",
                                "aliases": ["faróis", "headlights", "restauração faróis"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Pulido completo de carrocería",
                                "aliases": ["pulido completo", "full polish", "pulido total"],
                            },
                            "en": {
                                "label": "Full body polish",
                                "aliases": ["full polish", "body polish", "complete polish"],
                            },
                            "pt": {
                                "label": "Polimento completo de carroceria",
                                "aliases": ["polimento completo", "full polish", "polimento total"],
                            },
                        }
                    },
                ],
            },
        },
    },
    "SPECIALIZED": {
        "code": "SPECIALIZED",
        "orden": 9,
        "names": {
            "es": {
                "label": "Servicios Especializados",
                "aliases": ["especializado", "rectificación", "escape", "vidrios"],
            },
            "en": {
                "label": "Specialized Services",
                "aliases": ["specialized", "machine shop", "exhaust", "glass"],
            },
            "pt": {
                "label": "Serviços Especializados",
                "aliases": ["especializado", "retificação", "escapamento", "vidros"],
            },
        },
        "subcategorias": {
            "MACHINE_SHOP": {
                "code": "MACHINE_SHOP",
                "orden": 1,
                "names": {
                    "es": {
                        "label": "Rectificación de Motores",
                        "aliases": ["rectificación", "machine shop", "encamisado"],
                    },
                    "en": {
                        "label": "Engine Machining",
                        "aliases": ["machining", "machine shop", "boring"],
                    },
                    "pt": {
                        "label": "Retificação de Motores",
                        "aliases": ["retificação", "usinagem", "encamisamento"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Rectificación de motores",
                                "aliases": ["rectificación", "encamisado", "machine shop"],
                            },
                            "en": {
                                "label": "Engine machining",
                                "aliases": ["machining", "boring", "machine shop"],
                            },
                            "pt": {
                                "label": "Retificação de motores",
                                "aliases": ["retificação", "encamisamento", "usinagem"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Rectificado de culata",
                                "aliases": ["culata", "head resurfacing", "rectificar culata"],
                            },
                            "en": {
                                "label": "Cylinder head resurfacing",
                                "aliases": ["head resurfacing", "head machining", "head"],
                            },
                            "pt": {
                                "label": "Retificação de cabeçote",
                                "aliases": ["cabeçote", "retificar cabeçote", "usinagem cabeçote"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de válvulas",
                                "aliases": ["válvulas", "valve job", "reparación válvulas"],
                            },
                            "en": {
                                "label": "Valve job",
                                "aliases": ["valve job", "valves", "valve repair"],
                            },
                            "pt": {
                                "label": "Reparo de válvulas",
                                "aliases": ["válvulas", "valve job", "reparo válvulas"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Encamisado de cilindros",
                                "aliases": ["encamisado", "boring", "cilindros", "block boring"],
                            },
                            "en": {
                                "label": "Engine block boring",
                                "aliases": ["boring", "block boring", "cylinders"],
                            },
                            "pt": {
                                "label": "Encamisamento de cilindros",
                                "aliases": ["encamisamento", "boring", "cilindros"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Rectificado de volante",
                                "aliases": ["volante", "flywheel", "rectificar volante"],
                            },
                            "en": {
                                "label": "Flywheel grinding",
                                "aliases": ["flywheel", "flywheel grind", "flywheel resurface"],
                            },
                            "pt": {
                                "label": "Retificação de volante",
                                "aliases": ["volante", "flywheel", "retificar volante"],
                            },
                        }
                    },
                ],
            },
            "EXHAUST": {
                "code": "EXHAUST",
                "orden": 2,
                "names": {
                    "es": {
                        "label": "Sistema de Escape",
                        "aliases": ["escape", "mofles", "silenciador"],
                    },
                    "en": {
                        "label": "Exhaust System",
                        "aliases": ["exhaust", "muffler", "silencer"],
                    },
                    "pt": {
                        "label": "Sistema de Escapamento",
                        "aliases": ["escapamento", "silenciador", "mofles"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Reparación de sistema de escape",
                                "aliases": ["escape", "mofles", "silenciador"],
                            },
                            "en": {
                                "label": "Exhaust system repair",
                                "aliases": ["exhaust", "muffler", "silencer"],
                            },
                            "pt": {
                                "label": "Reparo de sistema de escapamento",
                                "aliases": ["escapamento", "silenciador", "mofles"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de silenciador",
                                "aliases": ["silenciador", "muffler", "mofle"],
                            },
                            "en": {
                                "label": "Muffler replacement",
                                "aliases": ["muffler", "silencer", "exhaust muffler"],
                            },
                            "pt": {
                                "label": "Troca de silenciador",
                                "aliases": ["silenciador", "muffler", "mofle"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de catalizador",
                                "aliases": ["catalizador", "catalytic converter", "convertidor"],
                            },
                            "en": {
                                "label": "Catalytic converter replacement",
                                "aliases": ["catalytic converter", "catalyst", "converter"],
                            },
                            "pt": {
                                "label": "Troca de catalisador",
                                "aliases": ["catalisador", "catalytic converter", "convertidor"],
                            },
                        }
                    },
                ],
            },
            "ACCESSORIES": {
                "code": "ACCESSORIES",
                "orden": 3,
                "names": {
                    "es": {
                        "label": "Accesorios e Instalaciones",
                        "aliases": ["accesorios", "instalación", "radios", "alarmas"],
                    },
                    "en": {
                        "label": "Accessories and Installation",
                        "aliases": ["accessories", "installation", "radios", "alarms"],
                    },
                    "pt": {
                        "label": "Acessórios e Instalações",
                        "aliases": ["acessórios", "instalação", "rádios", "alarmes"],
                    },
                },
                "servicios": [
                    {
                        "names": {
                            "es": {
                                "label": "Instalación de accesorios",
                                "aliases": ["accesorios", "instalación", "radios", "alarmas"],
                            },
                            "en": {
                                "label": "Accessory installation",
                                "aliases": ["accessories", "installation", "radios", "alarms"],
                            },
                            "pt": {
                                "label": "Instalação de acessórios",
                                "aliases": ["acessórios", "instalação", "rádios", "alarmes"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Vidrios y parabrisas",
                                "aliases": ["vidrios", "parabrisas", "cristales"],
                            },
                            "en": {
                                "label": "Glass and windshields",
                                "aliases": ["glass", "windshield", "windows"],
                            },
                            "pt": {
                                "label": "Vidros e para-brisas",
                                "aliases": ["vidros", "para-brisas", "cristais"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Cambio de parabrisas",
                                "aliases": ["parabrisas", "windshield", "cristal delantero"],
                            },
                            "en": {
                                "label": "Windshield replacement",
                                "aliases": ["windshield", "front glass", "windshield glass"],
                            },
                            "pt": {
                                "label": "Troca de para-brisas",
                                "aliases": ["para-brisas", "windshield", "vidro dianteiro"],
                            },
                        }
                    },
                    {
                        "names": {
                            "es": {
                                "label": "Instalación de accesorios personalizados",
                                "aliases": ["accesorios", "custom", "instalación accesorios"],
                            },
                            "en": {
                                "label": "Custom accessory installation",
                                "aliases": ["accessories", "custom", "accessory install"],
                            },
                            "pt": {
                                "label": "Instalação de acessórios personalizados",
                                "aliases": ["acessórios", "custom", "instalação acessórios"],
                            },
                        }
                    },
                ],
            },
        },
    },
}

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================


def get_or_create_empresa_maestra():
    """Obtiene o crea la empresa maestra (id=1) para servicios globales"""
    from django.contrib.auth.models import User

    try:
        empresa = Empresa.objects.get(id=1)
        print(f"✅ Empresa maestra encontrada: {empresa.nombre_taller}")
        return empresa
    except Empresa.DoesNotExist:
        # Crear usuario sistema si no existe
        user_sistema, _ = User.objects.get_or_create(
            username="sistema_catalogo_maestro",
            defaults={
                "email": "sistema@egarage.com",
                "is_active": False,  # Usuario inactivo, solo para la empresa maestra
            },
        )

        # Crear empresa maestra si no existe
        empresa = Empresa.objects.create(
            id=1,
            user=user_sistema,
            nombre_taller="Catálogo Maestro Global",
            empresa="Sistema eGarage",
            pais="CL",  # Default, se puede cambiar
            is_trial=False,
        )
        print(f"✅ Empresa maestra creada: {empresa.nombre_taller}")
        return empresa


def create_categoria(categoria_data, country="CL"):
    """Crea una categoría con sus nombres localizados"""
    categoria, created = CategoriaServicio.objects.get_or_create(
        country=country,
        code=categoria_data["code"],
        defaults={"activo": True},
    )

    if not created:
        categoria.activo = True
        categoria.save()

    # Crear nombres localizados
    for lang, name_data in categoria_data["names"].items():
        CategoriaServicioName.objects.update_or_create(
            categoria=categoria,
            language=lang,
            is_default=True,
            defaults={
                "label": name_data["label"],
                "aliases": name_data.get("aliases", []),
            },
        )

    return categoria


def create_subcategoria(subcategoria_data, categoria, country="CL"):
    """Crea una subcategoría con sus nombres localizados"""
    subcategoria, created = SubcategoriaServicio.objects.get_or_create(
        categoria=categoria,
        country=country,
        code=subcategoria_data["code"],
        defaults={"activo": True},
    )

    if not created:
        subcategoria.activo = True
        subcategoria.save()

    # Crear nombres localizados
    for lang, name_data in subcategoria_data["names"].items():
        SubcategoriaServicioName.objects.update_or_create(
            subcategoria=subcategoria,
            language=lang,
            is_default=True,
            defaults={
                "label": name_data["label"],
                "aliases": name_data.get("aliases", []),
            },
        )

    return subcategoria


def create_servicio(servicio_data, subcategoria, empresa, country="CL"):
    """Crea un servicio con sus nombres localizados"""
    # Usar el nombre en español como nombre base
    nombre_base = servicio_data["names"]["es"]["label"]

    servicio, created = Servicio.objects.get_or_create(
        empresa=empresa,
        nombre=nombre_base,
        categoria=subcategoria.categoria,
        subcategoria=subcategoria,
        defaults={"activo": True},
    )

    if not created:
        servicio.activo = True
        servicio.save()

    # Crear nombres localizados
    for lang, name_data in servicio_data["names"].items():
        ServicioName.objects.update_or_create(
            servicio=servicio,
            language=lang,
            is_default=True,
            defaults={
                "label": name_data["label"],
                "aliases": name_data.get("aliases", []),
            },
        )

    return servicio, created


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================


def seed_catalogo_maestro():
    """Función principal para poblar el catálogo maestro"""
    print("=" * 80)
    print("🚀 INICIANDO CARGA DE CATÁLOGO MAESTRO DE SERVICIOS")
    print("=" * 80)

    # Obtener o crear empresa maestra
    empresa_maestra = get_or_create_empresa_maestra()

    # Contadores
    categorias_creadas = 0
    subcategorias_creadas = 0
    servicios_creados = 0
    servicios_actualizados = 0

    # Procesar cada categoría
    for cat_key, cat_data in CATEGORIAS_SISTEMAS.items():
        print(f"\n📁 Procesando categoría: {cat_data['names']['es']['label']}")

        # Crear categoría para cada país
        categorias_por_pais = {}
        for country in ["CL", "MX", "PE", "VE", "US", "BR"]:
            categoria = create_categoria(cat_data, country)
            categorias_por_pais[country] = categoria
            if categoria:
                categorias_creadas += 1

        # Procesar subcategorías
        for sub_key, sub_data in cat_data.get("subcategorias", {}).items():
            print(f"  📂 Subcategoría: {sub_data['names']['es']['label']}")

            # Crear subcategoría para cada país
            subcategorias_por_pais = {}
            for country, categoria in categorias_por_pais.items():
                subcategoria = create_subcategoria(sub_data, categoria, country)
                subcategorias_por_pais[country] = subcategoria
                if subcategoria:
                    subcategorias_creadas += 1

            # Procesar servicios
            for servicio_data in sub_data.get("servicios", []):
                # Crear servicio para cada país (usando la empresa maestra)
                for country, subcategoria in subcategorias_por_pais.items():
                    servicio, created = create_servicio(
                        servicio_data, subcategoria, empresa_maestra, country
                    )
                    if created:
                        servicios_creados += 1
                    else:
                        servicios_actualizados += 1
                    print(f"    🔧 {servicio.nombre}")

    # Resumen final
    print("\n" + "=" * 80)
    print("✅ CARGA COMPLETADA")
    print("=" * 80)
    print(f"📊 Resumen:")
    print(f"   Categorías procesadas: {len(CATEGORIAS_SISTEMAS)}")
    print(f"   Subcategorías creadas: {subcategorias_creadas}")
    print(f"   Servicios creados: {servicios_creados}")
    print(f"   Servicios actualizados: {servicios_actualizados}")
    print(
        f"   Total servicios en catálogo: {Servicio.objects.filter(empresa=empresa_maestra).count()}"
    )
    print("=" * 80)


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    seed_catalogo_maestro()
