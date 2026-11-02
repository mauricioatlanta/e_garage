#!/usr/bin/env python
"""
Script para crear colores por defecto para clientes/subscriptores
Sigue la misma dinámica que el sistema de colores de vehículos
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.color_cliente import ColorCliente


def crear_colores_por_defecto():
    """Crea colores por defecto para ambos países"""
    print("🎨 Creando colores por defecto para clientes/subscriptores...")
    print("=" * 60)

    # Crear colores para Chile (español)
    print("🇨🇱 Creando colores para Chile (español)...")
    ColorCliente.get_colores_para_pais("CL")

    # Crear colores para USA (inglés)
    print("🇺🇸 Creando colores para USA (inglés)...")
    ColorCliente.get_colores_para_pais("US")

    # Mostrar resumen
    total_chile = ColorCliente.objects.filter(country="CL", activo=True).count()
    total_usa = ColorCliente.objects.filter(country="US", activo=True).count()
    total_general = ColorCliente.objects.filter(activo=True).count()

    print("\n📊 RESUMEN DE COLORES CREADOS:")
    print(f"   🇨🇱 Chile (español): {total_chile} colores")
    print(f"   🇺🇸 USA (inglés): {total_usa} colores")
    print(f"   📈 Total general: {total_general} colores")

    # Mostrar algunos ejemplos
    print("\n🎨 EJEMPLOS DE COLORES:")
    print("   Chile:")
    for color in ColorCliente.objects.filter(country="CL", activo=True)[:5]:
        print(f"     • {color.nombre} ({color.codigo_color})")

    print("   USA:")
    for color in ColorCliente.objects.filter(country="US", activo=True)[:5]:
        print(f"     • {color.nombre} ({color.codigo_color})")

    print("\n✅ Colores creados exitosamente!")
    print("   Los clientes ahora pueden ser identificados por colores según su país")


if __name__ == "__main__":
    crear_colores_por_defecto()
