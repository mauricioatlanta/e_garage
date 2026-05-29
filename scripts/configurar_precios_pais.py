#!/usr/bin/env python
"""
🇨🇱🇺🇸 Script para configurar precios de suscripciones por país
Asegura que Chile tenga precios en CLP y USA en USD
"""

import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from decimal import Decimal

from taller.models.precio_suscripcion import PrecioSuscripcion


def configurar_precios_chile():
    """Configura precios para Chile en CLP"""
    print("🇨🇱 Configurando precios para Chile (CLP)...")

    precios_chile = [
        {
            "tipo_plan": "mensual",
            "precio": Decimal("20000"),
            "moneda": "CLP",
            "nombre_plan": "Plan Mensual",
            "descripcion": "Plan flexible mensual con todas las funciones básicas",
            "usuarios_incluidos": 5,
            "api_incluida": False,
            "multisucursal": False,
        },
        {
            "tipo_plan": "semestral",
            "precio": Decimal("110000"),
            "moneda": "CLP",
            "nombre_plan": "Plan Semestral",
            "descripcion": "Plan semestral con descuento y funciones avanzadas",
            "usuarios_incluidos": 10,
            "api_incluida": True,
            "multisucursal": False,
        },
        {
            "tipo_plan": "anual",
            "precio": Decimal("200000"),
            "moneda": "CLP",
            "nombre_plan": "Plan Anual",
            "descripcion": "Plan anual con máximo descuento y todas las funciones",
            "usuarios_incluidos": 999,  # Ilimitados
            "api_incluida": True,
            "multisucursal": True,
        },
    ]

    for precio_data in precios_chile:
        precio, created = PrecioSuscripcion.objects.update_or_create(
            tipo_plan=precio_data["tipo_plan"], pais="CL", defaults=precio_data
        )
        status = "✅ CREADO" if created else "🔄 ACTUALIZADO"
        print(f"   {status}: {precio.nombre_plan} - ${precio.precio:,.0f} CLP")


def configurar_precios_usa():
    """Configura precios para USA en USD"""
    print("\n🇺🇸 Configurando precios para USA (USD)...")

    precios_usa = [
        {
            "tipo_plan": "mensual",
            "precio": Decimal("20.00"),
            "moneda": "USD",
            "nombre_plan": "Monthly Plan",
            "descripcion": "Flexible monthly plan with all basic features",
            "usuarios_incluidos": 5,
            "api_incluida": False,
            "multisucursal": False,
        },
        {
            "tipo_plan": "semestral",
            "precio": Decimal("110.00"),
            "moneda": "USD",
            "nombre_plan": "Semi-Annual Plan",
            "descripcion": "Semi-annual plan with discount and advanced features",
            "usuarios_incluidos": 10,
            "api_incluida": True,
            "multisucursal": False,
        },
        {
            "tipo_plan": "anual",
            "precio": Decimal("200.00"),
            "moneda": "USD",
            "nombre_plan": "Annual Plan",
            "descripcion": "Annual plan with maximum discount and all features",
            "usuarios_incluidos": 999,  # Ilimitados
            "api_incluida": True,
            "multisucursal": True,
        },
    ]

    for precio_data in precios_usa:
        precio, created = PrecioSuscripcion.objects.update_or_create(
            tipo_plan=precio_data["tipo_plan"], pais="US", defaults=precio_data
        )
        status = "✅ CREADO" if created else "🔄 ACTUALIZADO"
        print(f"   {status}: {precio.nombre_plan} - ${precio.precio:,.2f} USD")


def verificar_configuracion():
    """Verifica que los precios estén correctamente configurados"""
    print("\n📊 VERIFICACIÓN DE PRECIOS CONFIGURADOS:")
    print("=" * 50)

    for pais, nombre_pais in [("CL", "Chile"), ("US", "Estados Unidos")]:
        print(f"\n🏛️ {nombre_pais}:")
        precios = PrecioSuscripcion.objects.filter(pais=pais, activo=True).order_by("precio")

        if not precios.exists():
            print(f"   ❌ No hay precios configurados para {nombre_pais}")
            continue

        for precio in precios:
            print(f"   💰 {precio.get_tipo_plan_display()}: {precio.precio_formateado()}")
            print(f"      👥 Usuarios: {precio.usuarios_incluidos}")
            print(f"      🔧 API: {'✅' if precio.api_incluida else '❌'}")
            print(f"      🏢 Multi-sucursal: {'✅' if precio.multisucursal else '❌'}")
            print()


def main():
    print("🚀 CONFIGURADOR DE PRECIOS DE SUSCRIPCIONES eGARAGE")
    print("=" * 55)
    print("Configurando precios diferenciados por país...")
    print()

    try:
        # Configurar precios por país
        configurar_precios_chile()
        configurar_precios_usa()

        # Verificar configuración
        verificar_configuracion()

        print("\n🎉 ¡CONFIGURACIÓN DE PRECIOS COMPLETADA!")
        print("=" * 45)
        print("✅ Chile: Precios en CLP (sin decimales)")
        print("✅ USA: Precios en USD (con decimales)")
        print("\n📋 Los precios ahora se mostrarán automáticamente según el país del usuario")
        print("🌐 Vista de precios: /precios/")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Verifique que la base de datos esté disponible y las migraciones aplicadas")


if __name__ == "__main__":
    main()
