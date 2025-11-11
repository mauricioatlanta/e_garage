#!/usr/bin/env python
"""
Script para verificar datos de marcas y modelos en la base de datos
"""

import os
import sys
from pathlib import Path

import django

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()


def main():
    print("🔍 VERIFICACIÓN DE DATOS MARCAS Y MODELOS")
    print("=" * 50)

    try:
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo

        # Verificar marcas por país
        print("📊 MARCAS POR PAÍS:")
        marcas_cl = Marca.objects.filter(country="CL").count()
        marcas_us = Marca.objects.filter(country="US").count()
        marcas_total = Marca.objects.all().count()
        print(f"  🇨🇱 Chile: {marcas_cl} marcas")
        print(f"  🇺🇸 USA: {marcas_us} marcas")
        print(f"  📊 Total: {marcas_total} marcas")

        # Verificar modelos por país
        print("\n📊 MODELOS POR PAÍS:")
        modelos_cl = Modelo.objects.filter(country="CL").count()
        modelos_us = Modelo.objects.filter(country="US").count()
        modelos_total = Modelo.objects.all().count()
        print(f"  🇨🇱 Chile: {modelos_cl} modelos")
        print(f"  🇺🇸 USA: {modelos_us} modelos")
        print(f"  📊 Total: {modelos_total} modelos")

        # Mostrar algunas marcas de ejemplo
        print("\n🔍 MARCAS DE EJEMPLO (Chile):")
        for marca in Marca.objects.filter(country="CL")[:5]:
            modelos_count = Modelo.objects.filter(marca=marca, country="CL").count()
            print(f"  {marca.id}: {marca.nombre} ({modelos_count} modelos)")

        # Mostrar algunos modelos de ejemplo para la primera marca
        primera_marca = Marca.objects.filter(country="CL").first()
        if primera_marca:
            print(f"\n🔍 MODELOS PARA MARCA '{primera_marca.nombre}' (ID: {primera_marca.id}):")
            modelos = Modelo.objects.filter(marca=primera_marca, country="CL")[:5]
            for modelo in modelos:
                print(f"  {modelo.id}: {modelo.nombre}")

    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    main()
