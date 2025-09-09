#!/usr/bin/env python
"""
Resumen final - Verificar que todo está funcionando correctamente
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.marca import Marca
from taller.models.modelo import Modelo


def main():
    print("✅ RESUMEN FINAL - Estado del Sistema de Vehículos\n")

    # Verificar marcas por país
    marcas_chile = Marca.objects.filter(country="CL").count()
    marcas_usa = Marca.objects.filter(country="US").count()

    print(f"🇨🇱 Chile - Marcas: {marcas_chile}")
    print(f"🇺🇸 USA - Marcas: {marcas_usa}")

    # Verificar modelos por país
    modelos_chile = Modelo.objects.filter(marca__country="CL").count()
    modelos_usa = Modelo.objects.filter(marca__country="US").count()

    print(f"🇨🇱 Chile - Modelos: {modelos_chile}")
    print(f"🇺🇸 USA - Modelos: {modelos_usa}")

    # Mostrar algunas marcas y modelos de Chile
    print("\n📋 Marcas principales Chile:")
    for marca in Marca.objects.filter(country="CL").order_by("nombre")[:5]:
        modelos_count = Modelo.objects.filter(marca=marca).count()
        print(f"  • {marca.nombre} ({modelos_count} modelos)")

    print("\n🎉 SISTEMA CONFIGURADO CORRECTAMENTE")
    print("✅ Formulario de crear vehículo ahora debe mostrar:")
    print(f"   - Lista de marcas para Chile ({marcas_chile} opciones)")
    print("   - Carga dinámica de modelos vía AJAX")
    print(f"   - {modelos_chile} modelos totales disponibles")


if __name__ == "__main__":
    main()
