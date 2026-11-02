#!/usr/bin/env python
"""
Script para cargar servicios de ejemplo en el taller mecánico
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models import Empresa
from taller.servicios.models import (
    CategoriaServicio,
    CategoriaServicioName,
    Servicio,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)


def crear_servicios_ejemplo():
    """Crear servicios de ejemplo para taller mecánico"""

    # Obtener la primera empresa disponible
    try:
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ No se encontró ninguna empresa. Crea una empresa primero.")
            return
        print(f"🏢 Usando empresa: {empresa}")
    except Exception as e:
        print(f"❌ Error al obtener empresa: {e}")
        return

    # Servicios por categorías
    servicios_data = {
        "MOTOR": {
            "nombre": "Motor y Sistema de Combustión",
            "subcategorias": {
                "MANTENIMIENTO_MOTOR": {
                    "nombre": "Mantenimiento de Motor",
                    "servicios": [
                        "Cambio de aceite y filtro",
                        "Cambio de filtro de aire",
                        "Cambio de filtro de combustible",
                        "Limpieza de inyectores",
                        "Afinación de motor",
                        "Revisión de compresión",
                        "Cambio de bujías",
                        "Cambio de cables de bujía",
                        "Limpieza de cuerpo de aceleración",
                        "Cambio de correa de distribución",
                    ],
                },
                "REPARACION_MOTOR": {
                    "nombre": "Reparación de Motor",
                    "servicios": [
                        "Rectificación de motor",
                        "Cambio de pistones y anillos",
                        "Cambio de válvulas",
                        "Reparación de culata",
                        "Cambio de empaque de culata",
                        "Reparación de block de motor",
                        "Cambio de cigüeñal",
                        "Cambio de bielas",
                        "Balanceo de motor",
                        "Prueba de estanqueidad",
                    ],
                },
            },
        },
        "TRANSMISION": {
            "nombre": "Transmisión y Embrague",
            "subcategorias": {
                "MANTENIMIENTO_TRANSMISION": {
                    "nombre": "Mantenimiento de Transmisión",
                    "servicios": [
                        "Cambio de aceite de transmisión",
                        "Revisión de transmisión automática",
                        "Revisión de transmisión manual",
                        "Cambio de filtro de transmisión",
                        "Ajuste de bandas de transmisión",
                        "Limpieza de transmisión",
                        "Diagnóstico de transmisión",
                        "Cambio de líquido ATF",
                        "Revisión de diferencial",
                        "Cambio de aceite de diferencial",
                    ],
                },
                "EMBRAGUE": {
                    "nombre": "Sistema de Embrague",
                    "servicios": [
                        "Cambio de kit de embrague",
                        "Cambio de plato de embrague",
                        "Cambio de disco de embrague",
                        "Cambio de collarin de embrague",
                        "Ajuste de embrague",
                        "Cambio de cable de embrague",
                        "Sangrado de sistema hidráulico",
                        "Cambio de cilindro maestro",
                        "Cambio de cilindro esclavo",
                        "Revisión de volante",
                    ],
                },
            },
        },
        "FRENOS": {
            "nombre": "Sistema de Frenos",
            "subcategorias": {
                "MANTENIMIENTO_FRENOS": {
                    "nombre": "Mantenimiento de Frenos",
                    "servicios": [
                        "Cambio de pastillas de freno",
                        "Cambio de discos de freno",
                        "Cambio de tambores de freno",
                        "Cambio de zapatas de freno",
                        "Sangrado de frenos",
                        "Cambio de líquido de frenos",
                        "Revisión de sistema ABS",
                        "Cambio de cilindro de rueda",
                        "Cambio de cilindro maestro",
                        "Ajuste de freno de estacionamiento",
                    ],
                },
                "REPARACION_FRENOS": {
                    "nombre": "Reparación de Frenos",
                    "servicios": [
                        "Rectificación de discos",
                        "Rectificación de tambores",
                        "Reparación de cilindro maestro",
                        "Reparación de cilindro de rueda",
                        "Reparación de calipers",
                        "Reparación de sistema ABS",
                        "Reparación de sensor ABS",
                        "Reparación de bomba ABS",
                        "Reparación de freno de estacionamiento",
                        "Reparación de booster de frenos",
                    ],
                },
            },
        },
        "SUSPENSION": {
            "nombre": "Suspensión y Dirección",
            "subcategorias": {
                "SUSPENSION": {
                    "nombre": "Sistema de Suspensión",
                    "servicios": [
                        "Cambio de amortiguadores",
                        "Cambio de resortes",
                        "Cambio de terminales de dirección",
                        "Cambio de rótulas",
                        "Cambio de bujes",
                        "Alineación de ruedas",
                        "Balanceo de ruedas",
                        "Cambio de estabilizadoras",
                        "Cambio de brazos de suspensión",
                        "Revision de geometría",
                    ],
                },
                "DIRECCION": {
                    "nombre": "Sistema de Dirección",
                    "servicios": [
                        "Cambio de cremallera de dirección",
                        "Cambio de bomba hidráulica",
                        "Cambio de aceite hidráulico",
                        "Cambio de mangueras hidráulicas",
                        "Ajuste de dirección",
                        "Cambio de volante",
                        "Reparación de columna de dirección",
                        "Cambio de axiales",
                        "Sangrado de dirección hidráulica",
                        "Revisión de dirección asistida",
                    ],
                },
            },
        },
        "ELECTRICO": {
            "nombre": "Sistema Eléctrico",
            "subcategorias": {
                "BATERIA_ALTERNADOR": {
                    "nombre": "Batería y Carga",
                    "servicios": [
                        "Cambio de batería",
                        "Cambio de alternador",
                        "Cambio de motor de arranque",
                        "Revisión de sistema de carga",
                        "Revisión de sistema de arranque",
                        "Limpieza de terminales",
                        "Prueba de batería",
                        "Prueba de alternador",
                        "Prueba de motor de arranque",
                        "Revisión de consumo eléctrico",
                    ],
                },
                "LUCES_ACCESORIOS": {
                    "nombre": "Luces y Accesorios",
                    "servicios": [
                        "Cambio de focos delanteros",
                        "Cambio de focos traseros",
                        "Cambio de intermitentes",
                        "Revisión de sistema eléctrico",
                        "Instalación de accesorios",
                        "Reparación de cableado",
                        "Cambio de fusibles",
                        "Cambio de relés",
                        "Instalación de alarma",
                        "Instalación de estéreo",
                    ],
                },
            },
        },
        "AIRE_ACONDICIONADO": {
            "nombre": "Aire Acondicionado",
            "subcategorias": {
                "MANTENIMIENTO_AC": {
                    "nombre": "Mantenimiento A/C",
                    "servicios": [
                        "Carga de gas refrigerante",
                        "Cambio de filtro de habitáculo",
                        "Limpieza de evaporador",
                        "Limpieza de condensador",
                        "Revisión de sistema A/C",
                        "Cambio de compresor",
                        "Cambio de válvula de expansión",
                        "Reparación de fugas",
                        "Diagnóstico de A/C",
                        "Desinfección de sistema",
                    ],
                }
            },
        },
        "NEUMATICOS": {
            "nombre": "Neumáticos y Llantas",
            "subcategorias": {
                "SERVICIO_NEUMATICOS": {
                    "nombre": "Servicios de Neumáticos",
                    "servicios": [
                        "Cambio de neumáticos",
                        "Rotación de neumáticos",
                        "Reparación de neumáticos",
                        "Instalación de neumáticos nuevos",
                        "Cambio de válvulas",
                        "Parche de neumático",
                        "Revisión de presión",
                        "Calibrado de neumáticos",
                        "Cambio de llantas",
                        "Revisión de desgaste",
                    ],
                }
            },
        },
        "CARROCERIA": {
            "nombre": "Carrocería y Pintura",
            "subcategorias": {
                "HOJALATERIA": {
                    "nombre": "Hojalatería",
                    "servicios": [
                        "Reparación de abolladuras",
                        "Enderezado de carrocería",
                        "Soldadura de carrocería",
                        "Cambio de puertas",
                        "Cambio de guardafangos",
                        "Cambio de capó",
                        "Cambio de cajuela",
                        "Reparación de chasis",
                        "Instalación de accesorios",
                        "Modificaciones de carrocería",
                    ],
                },
                "PINTURA": {
                    "nombre": "Pintura y Acabados",
                    "servicios": [
                        "Pintura completa",
                        "Pintura parcial",
                        "Retoque de pintura",
                        "Pulido de carrocería",
                        "Encerado",
                        "Detallado completo",
                        "Aplicación de cera",
                        "Limpieza profunda",
                        "Restauración de pintura",
                        "Protección de pintura",
                    ],
                },
            },
        },
    }

    print("🚀 Iniciando carga de servicios de ejemplo...")

    total_servicios = 0

    for cat_code, cat_data in servicios_data.items():
        # Crear categoría
        categoria, created = CategoriaServicio.objects.get_or_create(
            country="CL",
            code=cat_code,
        )

        if created:
            print(f"✅ Categoría creada: {cat_code}")

        # Crear nombre de categoría
        cat_name, created = CategoriaServicioName.objects.get_or_create(
            categoria=categoria,
            language="es",
            is_default=True,
            defaults={"label": cat_data["nombre"]},
        )

        # Procesar subcategorías
        for subcat_code, subcat_data in cat_data["subcategorias"].items():
            # Crear subcategoría
            subcategoria, created = SubcategoriaServicio.objects.get_or_create(
                categoria=categoria,
                country="CL",
                code=subcat_code,
            )

            if created:
                print(f"✅ Subcategoría creada: {subcat_code}")

            # Crear nombre de subcategoría
            subcat_name, created = SubcategoriaServicioName.objects.get_or_create(
                subcategoria=subcategoria,
                language="es",
                is_default=True,
                defaults={"label": subcat_data["nombre"]},
            )

            # Crear servicios
            for servicio_nombre in subcat_data["servicios"]:
                servicio, created = Servicio.objects.get_or_create(
                    empresa=empresa,
                    nombre=servicio_nombre,
                    categoria=categoria,
                    subcategoria=subcategoria,
                )

                if created:
                    total_servicios += 1
                    print(f"  ➕ Servicio: {servicio_nombre}")

    print("\n🎉 ¡Carga completada!")
    print(f"📊 Total de servicios creados: {total_servicios}")
    print(f"📊 Total de categorías: {CategoriaServicio.objects.count()}")
    print(f"📊 Total de subcategorías: {SubcategoriaServicio.objects.count()}")


if __name__ == "__main__":
    crear_servicios_ejemplo()
