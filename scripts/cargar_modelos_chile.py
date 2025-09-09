#!/usr/bin/env python
"""
Script para cargar modelos comunes de vehículos para marcas en Chile
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.marca import Marca
from taller.models.modelo import Modelo


def main():
    print("🚙 Cargando modelos de vehículos para Chile\n")

    # Definir modelos por marca
    modelos_por_marca = {
        "Toyota": [
            "Corolla",
            "Yaris",
            "RAV4",
            "Camry",
            "Highlander",
            "Prius",
            "Hilux",
            "Land Cruiser",
            "Avanza",
            "Rush",
            "C-HR",
            "Vitz",
        ],
        "Ford": [
            "Focus",
            "Fiesta",
            "Escape",
            "Explorer",
            "F-150",
            "Ranger",
            "EcoSport",
            "Mondeo",
            "Edge",
            "Expedition",
            "Transit",
        ],
        "Chevrolet": [
            "Cruze",
            "Sonic",
            "Spark",
            "Captiva",
            "Tracker",
            "Silverado",
            "Tahoe",
            "Onix",
            "Prisma",
            "S10",
            "Trailblazer",
        ],
        "Nissan": [
            "Sentra",
            "Versa",
            "Altima",
            "X-Trail",
            "Qashqai",
            "Pathfinder",
            "Frontier",
            "March",
            "Kicks",
            "Murano",
            "Navara",
        ],
        "Hyundai": [
            "Accent",
            "Elantra",
            "Tucson",
            "Santa Fe",
            "i10",
            "i20",
            "Veloster",
            "Sonata",
            "Creta",
            "Grand i10",
        ],
    }

    total_creados = 0
    total_existentes = 0

    for marca_nombre, modelos_lista in modelos_por_marca.items():
        try:
            marca = Marca.objects.get(nombre=marca_nombre, country="CL")
            print(f"🚗 Procesando marca: {marca_nombre}")

            marca_creados = 0
            marca_existentes = 0

            for modelo_nombre in modelos_lista:
                modelo, created = Modelo.objects.get_or_create(
                    nombre=modelo_nombre,
                    marca=marca,
                    defaults={"nombre": modelo_nombre, "marca": marca},
                )

                if created:
                    print(f"  ✅ Modelo creado: {modelo_nombre}")
                    marca_creados += 1
                    total_creados += 1
                else:
                    print(f"  📍 Modelo ya existe: {modelo_nombre}")
                    marca_existentes += 1
                    total_existentes += 1

            print(
                f"  📊 {marca_nombre}: {marca_creados} creados, {marca_existentes} existentes"
            )
            print()

        except Marca.DoesNotExist:
            print(f"❌ Error: Marca {marca_nombre} no encontrada")
            continue

    print("🎉 RESUMEN FINAL:")
    print(f"✅ Total modelos creados: {total_creados}")
    print(f"📍 Total modelos ya existentes: {total_existentes}")
    print(
        f"🚙 Total modelos Chile: {Modelo.objects.filter(marca__country='CL').count()}"
    )


if __name__ == "__main__":
    main()
