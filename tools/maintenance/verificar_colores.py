#!/usr/bin/env python
"""
Script para verificar colores de vehículos en la base de datos
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
    print("🎨 VERIFICACIÓN DE COLORES DE VEHÍCULOS")
    print("=" * 50)

    try:
        from taller.models.extras_vehiculo import ColorVehiculo

        # Verificar todos los colores
        colores = ColorVehiculo.objects.all().order_by("nombre")
        print(f"📊 Total colores: {colores.count()}")

        print("\n🎨 COLORES EN BASE DE DATOS:")
        for color in colores:
            print(f"  {color.id}: {color.nombre}")

        # Detectar si hay colores en inglés
        colores_inglés = []
        colores_español = []

        colores_inglés_keywords = [
            "red",
            "blue",
            "green",
            "black",
            "white",
            "yellow",
            "gray",
            "grey",
            "brown",
            "silver",
            "gold",
        ]
        colores_español_keywords = [
            "rojo",
            "azul",
            "verde",
            "negro",
            "blanco",
            "amarillo",
            "gris",
            "café",
            "marrón",
            "plateado",
            "dorado",
        ]

        for color in colores:
            nombre_lower = color.nombre.lower()
            if any(eng in nombre_lower for eng in colores_inglés_keywords):
                colores_inglés.append(color.nombre)
            elif any(esp in nombre_lower for esp in colores_español_keywords):
                colores_español.append(color.nombre)

        print(f"\n🇺🇸 COLORES EN INGLÉS ({len(colores_inglés)}):")
        for color in colores_inglés:
            print(f"  - {color}")

        print(f"\n🇨🇱 COLORES EN ESPAÑOL ({len(colores_español)}):")
        for color in colores_español:
            print(f"  - {color}")

        print("\n📊 RESUMEN:")
        print(f"  Total: {colores.count()}")
        print(f"  En inglés: {len(colores_inglés)}")
        print(f"  En español: {len(colores_español)}")
        print(
            f"  Otros/neutros: {colores.count() - len(colores_inglés) - len(colores_español)}"
        )

    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    main()
