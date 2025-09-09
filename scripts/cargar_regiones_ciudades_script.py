#!/usr/bin/env python
"""
Script para cargar regiones y ciudades desde regiones_ciudades.json
"""

import json
import os
import sys

import django

# Configurar Django - usar la misma configuración que el servidor funcionando
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from taller.models.region_ciudad import TallerCiudad, TallerRegion


def cargar_regiones_ciudades():
    """Carga regiones y ciudades desde el archivo JSON"""

    # Leer el archivo JSON
    with open("regiones_ciudades.json", encoding="utf-8") as f:
        data = json.load(f)

    print("🚀 Iniciando carga de regiones y ciudades...")

    # Limpiar datos existentes
    print("🧹 Limpiando datos existentes...")
    TallerCiudad.objects.all().delete()
    TallerRegion.objects.all().delete()

    regiones_creadas = 0
    ciudades_creadas = 0

    for item in data:
        # Crear la región
        region, created = TallerRegion.objects.get_or_create(nombre=item["region"])

        if created:
            regiones_creadas += 1
            print(f"✅ Región creada: {region.nombre}")

        # Crear las ciudades para esta región
        for ciudad_nombre in item["ciudades"]:
            ciudad, created = TallerCiudad.objects.get_or_create(
                nombre=ciudad_nombre, region=region
            )

            if created:
                ciudades_creadas += 1
                print(f"   🏙️ Ciudad creada: {ciudad.nombre}")

    print("\n🎉 ¡Proceso completado!")
    print(f"📊 Regiones creadas: {regiones_creadas}")
    print(f"🏙️ Ciudades creadas: {ciudades_creadas}")

    # Verificar datos
    total_regiones = TallerRegion.objects.count()
    total_ciudades = TallerCiudad.objects.count()
    print("\n📈 Total en base de datos:")
    print(f"   Regiones: {total_regiones}")
    print(f"   Ciudades: {total_ciudades}")


if __name__ == "__main__":
    cargar_regiones_ciudades()
