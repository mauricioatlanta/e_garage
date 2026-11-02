#!/usr/bin/env python
"""
Script para actualizar los precios de USA a $20, $100, $200
Todos los planes tienen las mismas características, la diferencia es el ahorro
"""

import os
import sys

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.precio_suscripcion import PrecioSuscripcion


def actualizar_precios_usa():
    print("=" * 60)
    print("ACTUALIZANDO PRECIOS USA - CARACTERÍSTICAS IGUALES")
    print("=" * 60)
    print()

    # Características IGUALES para todos los planes
    caracteristicas_base = {
        "documentos_ilimitados": True,
        "usuarios_incluidos": 999,  # Ilimitados (representado con número alto)
        "soporte_prioritario": True,
        "reportes_avanzados": True,
        "diagnostico_ia": True,
        "api_incluida": True,
        "multisucursal": True,
    }

    # Precios con cálculo de ahorro
    # Precio mensual: $20
    # Semestral: 6 meses x $20 = $120, pero cobras $100 → Ahorro $20 (17% off)
    # Anual: 12 meses x $20 = $240, pero cobras $200 → Ahorro $40 (17% off)

    precios_correctos = {
        "mensual": {
            "precio": 20.00,
            "nombre": "Monthly Plan USA",
        },
        "semestral": {
            "precio": 100.00,
            "nombre": "Semi-Annual Plan USA",
        },
        "anual": {
            "precio": 200.00,
            "nombre": "Annual Plan USA",
        },
    }

    for tipo_plan, datos in precios_correctos.items():
        # Buscar o crear el precio con características iguales
        precio, created = PrecioSuscripcion.objects.update_or_create(
            pais="US",
            tipo_plan=tipo_plan,
            activo=True,
            defaults={
                "precio": datos["precio"],
                "moneda": "USD",
                "nombre_plan": datos["nombre"],
                **caracteristicas_base,  # Mismas características para todos
            },
        )

        if created:
            print(f"✅ CREADO: {datos['nombre']}")
        else:
            print(f"✅ ACTUALIZADO: {datos['nombre']}")

        print(f"   Precio: ${datos['precio']:.2f} USD")

        # Calcular ahorro
        if tipo_plan == "semestral":
            ahorro = (20 * 6) - 100
            porcentaje = (ahorro / (20 * 6)) * 100
            print(f"   Ahorro: ${ahorro:.0f} USD ({porcentaje:.0f}% off vs monthly)")
        elif tipo_plan == "anual":
            ahorro = (20 * 12) - 200
            porcentaje = (ahorro / (20 * 12)) * 100
            print(f"   Ahorro: ${ahorro:.0f} USD ({porcentaje:.0f}% off vs monthly)")

        print()

    print("=" * 60)
    print("CARACTERÍSTICAS (IGUALES PARA TODOS LOS PLANES)")
    print("=" * 60)
    print("✅ Unlimited documents")
    print("✅ Unlimited users")
    print("✅ Priority support")
    print("✅ Advanced reports")
    print("✅ AI diagnostics included")
    print("✅ Custom API")
    print("✅ Multi-location support")
    print()

    print("=" * 60)
    print("PRECIOS Y AHORROS")
    print("=" * 60)
    print("Monthly:      $20/month  (no discount)")
    print("Semi-Annual:  $100/6mo   (Save $20 - 17% off)")
    print("Annual:       $200/year  (Save $40 - 17% off)")
    print()


if __name__ == "__main__":
    actualizar_precios_usa()
