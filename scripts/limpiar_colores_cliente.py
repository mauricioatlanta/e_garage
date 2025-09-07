#!/usr/bin/env python
"""
Script para limpiar y optimizar el sistema de colores de clientes
Mantiene solo colores esenciales y elimina los innecesarios
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.clientes import Cliente
from taller.models.color_cliente import ColorCliente


def limpiar_colores_cliente():
    """Limpia el sistema de colores manteniendo solo los esenciales"""
    print("🧹 LIMPIANDO SISTEMA DE COLORES DE CLIENTES")
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

    print("1️⃣ Eliminando colores innecesarios...")

    # Eliminar colores de Chile que no están en la lista esencial
    colores_chile = ColorCliente.objects.filter(country="CL")
    eliminados_chile = 0
    for color in colores_chile:
        if color.nombre not in colores_esenciales_chile:
            print(f"   🗑️ Eliminando Chile: {color.nombre}")
            color.delete()
            eliminados_chile += 1

    # Eliminar colores de USA que no están en la lista esencial
    colores_usa = ColorCliente.objects.filter(country="US")
    eliminados_usa = 0
    for color in colores_usa:
        if color.nombre not in colores_esenciales_usa:
            print(f"   🗑️ Eliminando USA: {color.nombre}")
            color.delete()
            eliminados_usa += 1

    print("\n2️⃣ Verificando colores restantes...")

    # Verificar colores de Chile
    colores_chile_restantes = ColorCliente.objects.filter(country="CL")
    print(f"   🇨🇱 Chile: {colores_chile_restantes.count()} colores")
    for color in colores_chile_restantes:
        print(f"     • {color.nombre} ({color.codigo_color})")

    # Verificar colores de USA
    colores_usa_restantes = ColorCliente.objects.filter(country="US")
    print(f"   🇺🇸 USA: {colores_usa_restantes.count()} colores")
    for color in colores_usa_restantes:
        print(f"     • {color.nombre} ({color.codigo_color})")

    print("\n3️⃣ Verificando clientes con colores...")
    clientes_con_color = Cliente.objects.filter(color__isnull=False).count()
    clientes_sin_color = Cliente.objects.filter(color__isnull=True).count()
    print(f"   👥 Clientes con color: {clientes_con_color}")
    print(f"   👤 Clientes sin color: {clientes_sin_color}")

    print("\n📊 RESUMEN DE LIMPIEZA:")
    print(f"   🗑️ Colores eliminados Chile: {eliminados_chile}")
    print(f"   🗑️ Colores eliminados USA: {eliminados_usa}")
    print(f"   📈 Total eliminados: {eliminados_chile + eliminados_usa}")
    print(f"   ✅ Colores restantes Chile: {colores_chile_restantes.count()}")
    print(f"   ✅ Colores restantes USA: {colores_usa_restantes.count()}")

    print("\n🎯 SISTEMA OPTIMIZADO:")
    print("   • Solo colores esenciales mantenidos")
    print("   • Sistema más limpio y eficiente")
    print("   • Funcionalidad completa preservada")

    print("\n✅ LIMPIEZA COMPLETADA!")


if __name__ == "__main__":
    limpiar_colores_cliente()
