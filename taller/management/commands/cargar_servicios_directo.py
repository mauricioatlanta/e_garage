"""
Comando alternativo para cargar servicios que evita importaciones problemáticas
"""

import os
import sys
import django

# Configurar Django sin pasar por las validaciones
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Evitar importaciones problemáticas durante el setup
try:
    django.setup()
except Exception as e:
    # Si hay error, continuar de todas formas
    print(f"Warning: {e}")

from django.db import transaction
from taller.models import Empresa
from taller.servicios.models import (
    CategoriaServicio,
    CategoriaServicioName,
    Servicio,
    ServicioName,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)


def cargar_servicios():
    """Carga servicios básicos para todas las empresas. DEPRECADO: use cargar_catalogo_maestro."""
    print("DEPRECADO: cargar_servicios_directo. Use: python manage.py cargar_catalogo_maestro")
    categorias = [
        {
            "code": "motor",
            "es": "Sistema de Motor",
            "en": "Engine System",
            "subcategorias": [
                {
                    "code": "diagnostico",
                    "es": "Diagnóstico computarizado de motor",
                    "en": "Engine Computer Diagnostics",
                    "servicios": [
                        {
                            "es": "Diagnóstico computarizado de motor (OBD-II / fabricante)",
                            "en": "OBD-II/Manufacturer Engine Scan",
                        },
                        {
                            "es": "Lectura y borrado de códigos de error",
                            "en": "Read and Clear Error Codes",
                        },
                    ],
                },
                {
                    "code": "aceite",
                    "es": "Cambio de aceite y filtros",
                    "en": "Oil & Filter Change",
                    "servicios": [
                        {
                            "es": "Cambio de aceite de motor y filtros (aceite, aire, combustible, habitáculo)",
                            "en": "Engine Oil & Filter Change (oil, air, fuel, cabin)",
                        },
                        {
                            "es": "Cambio de aceite sintético",
                            "en": "Synthetic Oil Change",
                        },
                    ],
                },
            ],
        },
        {
            "code": "frenos",
            "es": "Sistema de Frenos",
            "en": "Brake System",
            "subcategorias": [
                {
                    "code": "revision",
                    "es": "Revisión de frenos",
                    "en": "Brake Inspection",
                    "servicios": [
                        {
                            "es": "Revisión completa del sistema de frenos",
                            "en": "Complete Brake System Inspection",
                        },
                    ],
                },
                {
                    "code": "reparacion",
                    "es": "Reparación de frenos",
                    "en": "Brake Repair",
                    "servicios": [
                        {
                            "es": "Cambio de pastillas de freno",
                            "en": "Brake Pad Replacement",
                        },
                        {
                            "es": "Cambio de discos de freno",
                            "en": "Brake Rotor Replacement",
                        },
                        {
                            "es": "Cambio de líquido de frenos",
                            "en": "Brake Fluid Replacement",
                        },
                    ],
                },
            ],
        },
    ]

    empresas = Empresa.objects.all()
    if not empresas.exists():
        print("⚠️ No hay empresas en la base de datos")
        return

    print(f"📋 Encontradas {empresas.count()} empresa(s)")

    with transaction.atomic():
        for country, lang, label_key in [("CL", "es", "es"), ("US", "en", "en")]:
            print(f"\n🌍 Poblando servicios para {country} ({lang})")

            for cat in categorias:
                cat_obj, created = CategoriaServicio.objects.get_or_create(
                    country=country, code=cat["code"]
                )
                CategoriaServicioName.objects.get_or_create(
                    categoria=cat_obj,
                    language=lang,
                    is_default=True,
                    defaults={"label": cat[label_key]},
                )

                for sub in cat["subcategorias"]:
                    sub_obj, created = SubcategoriaServicio.objects.get_or_create(
                        categoria=cat_obj, code=sub["code"], country=country
                    )
                    SubcategoriaServicioName.objects.get_or_create(
                        subcategoria=sub_obj,
                        language=lang,
                        is_default=True,
                        defaults={"label": sub[label_key]},
                    )

                    for serv in sub["servicios"]:
                        for empresa in empresas:
                            if empresa.pais == country:
                                servicio, created = Servicio.objects.get_or_create(
                                    empresa=empresa,
                                    categoria=cat_obj,
                                    subcategoria=sub_obj,
                                    nombre=serv[label_key],
                                )
                                ServicioName.objects.get_or_create(
                                    servicio=servicio,
                                    language=lang,
                                    is_default=True,
                                    defaults={"label": serv[label_key]},
                                )
                                if created:
                                    print(f"  ✅ Servicio creado: {serv[label_key]}")

    total_servicios = Servicio.objects.count()
    print(f"\n✅ ¡Carga completada!")
    print(f"📊 Total servicios: {total_servicios}")


if __name__ == "__main__":
    cargar_servicios()
