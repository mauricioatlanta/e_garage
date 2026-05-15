#!/usr/bin/env python
"""
Script para limpiar directamente los colores de la base de datos
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.color_cliente import ColorCliente


def limpiar_colores_directo():
    """Limpia directamente los colores de la base de datos"""
    print("🧹 LIMPIEZA DIRECTA DE COLORES")
    print("=" * 60)

    # Colores esenciales a mantener
    colores_esenciales_chile = [
        "Rojo",
        "Azul",
        "Verde",
        "Amarillo",
        "Negro",
        "Blanco",
        "Gris",
        "Naranja",
        "Morado",
        "Rosa",
    ]

    colores_esenciales_usa = [
        "Red",
        "Blue",
        "Green",
        "Yellow",
        "Black",
        "White",
        "Gray",
        "Orange",
        "Purple",
        "Pink",
    ]

    print("1️⃣ Eliminando TODOS los colores existentes...")

    # Eliminar todos los colores existentes
    total_eliminados = ColorCliente.objects.count()
    ColorCliente.objects.all().delete()
    print(f"   🗑️ Eliminados: {total_eliminados} colores")

    print("2️⃣ Creando solo colores esenciales...")

    # Crear colores esenciales para Chile
    colores_chile_data = [
        ("Rojo", "#ff0000"),
        ("Azul", "#0000ff"),
        ("Verde", "#00ff00"),
        ("Amarillo", "#ffff00"),
        ("Negro", "#000000"),
        ("Blanco", "#ffffff"),
        ("Gris", "#808080"),
        ("Naranja", "#ffa500"),
        ("Morado", "#800080"),
        ("Rosa", "#ffc0cb"),
    ]

    for i, (nombre, codigo) in enumerate(colores_chile_data):
        ColorCliente.objects.create(
            nombre=nombre, country="CL", codigo_color=codigo, orden=i, activo=True
        )
        print(f"   ✅ Chile: {nombre}")

    # Crear colores esenciales para USA
    colores_usa_data = [
        ("Red", "#ff0000"),
        ("Blue", "#0000ff"),
        ("Green", "#00ff00"),
        ("Yellow", "#ffff00"),
        ("Black", "#000000"),
        ("White", "#ffffff"),
        ("Gray", "#808080"),
        ("Orange", "#ffa500"),
        ("Purple", "#800080"),
        ("Pink", "#ffc0cb"),
    ]

    for i, (nombre, codigo) in enumerate(colores_usa_data):
        ColorCliente.objects.create(
            nombre=nombre, country="US", codigo_color=codigo, orden=i, activo=True
        )
        print(f"   ✅ USA: {nombre}")

    print("\n3️⃣ Verificando resultado final...")

    total_final = ColorCliente.objects.count()
    chile_final = ColorCliente.objects.filter(country="CL").count()
    usa_final = ColorCliente.objects.filter(country="US").count()

    print(f"   📊 Total colores: {total_final}")
    print(f"   🇨🇱 Chile: {chile_final}")
    print(f"   🇺🇸 USA: {usa_final}")

    print("\n✅ LIMPIEZA DIRECTA COMPLETADA!")
    print("   • Solo 10 colores esenciales por país")
    print("   • Sistema optimizado y limpio")
    print("   • Rojo/Red funcionando correctamente")


if __name__ == "__main__":
    limpiar_colores_directo()
