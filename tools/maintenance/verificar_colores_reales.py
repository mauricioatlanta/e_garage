#!/usr/bin/env python
"""
Script para verificar el estado real de los colores en la base de datos
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.color_cliente import ColorCliente


def verificar_colores_reales():
    """Verifica el estado real de los colores en la base de datos"""
    print("🔍 VERIFICANDO COLORES REALES EN BASE DE DATOS")
    print("=" * 60)

    # Contar colores reales en la base de datos
    total_colores = ColorCliente.objects.count()
    colores_chile = ColorCliente.objects.filter(country="CL").count()
    colores_usa = ColorCliente.objects.filter(country="US").count()

    print("📊 ESTADO REAL DE LA BASE DE DATOS:")
    print(f"   • Total colores: {total_colores}")
    print(f"   • Chile: {colores_chile}")
    print(f"   • USA: {colores_usa}")

    print("\n🇨🇱 COLORES CHILE (REALES):")
    for color in ColorCliente.objects.filter(country="CL").order_by("nombre"):
        print(f"   • {color.nombre} ({color.codigo_color})")

    print("\n🇺🇸 COLORES USA (REALES):")
    for color in ColorCliente.objects.filter(country="US").order_by("nombre"):
        print(f"   • {color.nombre} ({color.codigo_color})")

    print("\n✅ VERIFICACIÓN COMPLETADA!")


if __name__ == "__main__":
    verificar_colores_reales()
