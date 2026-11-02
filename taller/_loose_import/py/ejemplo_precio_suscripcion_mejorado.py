#!/usr/bin/env python
"""
Ejemplo de uso del modelo PrecioSuscripcion mejorado

Este script demuestra las nuevas funcionalidades:
- Enums con TextChoices
- Manager con métodos de conveniencia
- Validaciones en clean()
- Unicidad condicional
- Métodos de formateo
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.precio_suscripcion import PrecioSuscripcion


def demo_mejoras_precio_suscripcion():
    """Demuestra las mejoras del modelo PrecioSuscripcion"""

    print("🚀 DEMOSTRACIÓN DE MEJORAS EN PRECIOSUSCRIPCION")
    print("=" * 60)

    # 1. Uso de Enums (TextChoices)
    print("\n1️⃣ ENUMS CON TEXTCHOICES:")
    print(f"   Tipos de plan disponibles: {PrecioSuscripcion.TipoPlan.choices}")
    print(f"   Países disponibles: {PrecioSuscripcion.Pais.choices}")

    # 2. Manager con métodos de conveniencia
    print("\n2️⃣ MANAGER CON MÉTODOS DE CONVENIENCIA:")

    # Obtener todos los precios activos
    activos = PrecioSuscripcion.objects.activos()
    print(f"   Precios activos: {activos.count()}")

    # Obtener precios para Chile
    chile = PrecioSuscripcion.objects.para_pais("CL")
    print(f"   Precios para Chile: {chile.count()}")

    # Obtener precio vigente específico
    vigente_chile_mensual = PrecioSuscripcion.objects.vigente("CL", "mensual")
    if vigente_chile_mensual:
        print(f"   Plan mensual vigente en Chile: {vigente_chile_mensual}")
    else:
        print("   No hay plan mensual vigente en Chile")

    # 3. Validaciones en clean()
    print("\n3️⃣ VALIDACIONES EN CLEAN():")

    # Crear un precio de prueba (sin guardar)
    precio_test = PrecioSuscripcion(
        tipo_plan=PrecioSuscripcion.TipoPlan.MENSUAL,
        pais=PrecioSuscripcion.Pais.CL,
        precio=-100,  # Precio negativo (debería fallar)
        usuarios_incluidos=0,  # Menos de 1 usuario (debería fallar)
        moneda="USD",  # Moneda incorrecta para Chile (debería normalizarse)
    )

    try:
        precio_test.clean()
        print("   ❌ Validación falló: debería haber errores")
    except Exception as e:
        print(f"   ✅ Validación funcionó: {e}")

    # 4. Formateo de precios
    print("\n4️⃣ FORMATEO DE PRECIOS:")

    # Crear ejemplos de precios
    precio_cl = PrecioSuscripcion(
        pais=PrecioSuscripcion.Pais.CL,
        precio=25000,
        tipo_plan=PrecioSuscripcion.TipoPlan.MENSUAL,
    )
    precio_us = PrecioSuscripcion(
        pais=PrecioSuscripcion.Pais.US,
        precio=25.99,
        tipo_plan=PrecioSuscripcion.TipoPlan.MENSUAL,
    )

    print(f"   Precio Chile: {precio_cl.precio_formateado()}")
    print(f"   Precio USA: {precio_us.precio_formateado()}")

    # 5. Lista de características
    print("\n5️⃣ LISTA DE CARACTERÍSTICAS:")

    precio_completo = PrecioSuscripcion(
        pais=PrecioSuscripcion.Pais.CL,
        tipo_plan=PrecioSuscripcion.TipoPlan.ANUAL,
        precio=200000,
        usuarios_incluidos=10,
        documentos_ilimitados=True,
        reportes_avanzados=True,
        diagnostico_ia=True,
        soporte_prioritario=True,
        api_incluida=True,
        multisucursal=False,
    )

    caracteristicas = precio_completo.caracteristicas_list()
    print("   Características del plan anual:")
    for i, caracteristica in enumerate(caracteristicas, 1):
        print(f"     {i}. {caracteristica}")

    # 6. Unicidad condicional
    print("\n6️⃣ UNICIDAD CONDICIONAL:")
    print("   ✅ Permite múltiples registros inactivos del mismo plan/país")
    print("   ✅ Solo permite UN registro activo por plan/país")
    print("   ✅ Ideal para mantener histórico de precios")

    # 7. Métodos de clase
    print("\n7️⃣ MÉTODOS DE CLASE:")

    vigente = PrecioSuscripcion.get_vigente("CL", "mensual")
    if vigente:
        print(f"   Plan mensual vigente en Chile: {vigente}")
    else:
        print("   No hay plan mensual vigente en Chile")

    print("\n" + "=" * 60)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("\n💡 BENEFICIOS DE LAS MEJORAS:")
    print("   🔒 Validaciones robustas previenen datos incorrectos")
    print("   ⚡ Manager optimizado para consultas comunes")
    print("   📊 Unicidad condicional permite histórico")
    print("   🎨 Formateo consistente por país")
    print("   🛠️ API limpia y fácil de usar")
    print("   🚀 Índices optimizados para rendimiento")


def crear_datos_demo():
    """Crea datos de demostración si no existen"""

    print("\n🔧 CREANDO DATOS DE DEMOSTRACIÓN...")

    # Planes para Chile
    planes_chile = [
        {
            "tipo_plan": PrecioSuscripcion.TipoPlan.MENSUAL,
            "precio": 25000,
            "usuarios_incluidos": 5,
            "nombre_plan": "Plan Mensual Chile",
        },
        {
            "tipo_plan": PrecioSuscripcion.TipoPlan.ANUAL,
            "precio": 200000,
            "usuarios_incluidos": 10,
            "nombre_plan": "Plan Anual Chile",
            "api_incluida": True,
        },
    ]

    # Planes para USA
    planes_usa = [
        {
            "tipo_plan": PrecioSuscripcion.TipoPlan.MENSUAL,
            "precio": 25.99,
            "usuarios_incluidos": 5,
            "nombre_plan": "Monthly Plan USA",
        },
        {
            "tipo_plan": PrecioSuscripcion.TipoPlan.ANUAL,
            "precio": 199.99,
            "usuarios_incluidos": 10,
            "nombre_plan": "Annual Plan USA",
            "api_incluida": True,
        },
    ]

    for plan_data in planes_chile:
        plan_data["pais"] = PrecioSuscripcion.Pais.CL
        precio, created = PrecioSuscripcion.objects.get_or_create(
            tipo_plan=plan_data["tipo_plan"], pais=plan_data["pais"], defaults=plan_data
        )
        if created:
            print(f"   ✅ Creado: {precio}")
        else:
            print(f"   ℹ️ Ya existe: {precio}")

    for plan_data in planes_usa:
        plan_data["pais"] = PrecioSuscripcion.Pais.US
        precio, created = PrecioSuscripcion.objects.get_or_create(
            tipo_plan=plan_data["tipo_plan"], pais=plan_data["pais"], defaults=plan_data
        )
        if created:
            print(f"   ✅ Creado: {precio}")
        else:
            print(f"   ℹ️ Ya existe: {precio}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Demo de mejoras en PrecioSuscripcion")
    parser.add_argument("--create-demo", action="store_true", help="Crear datos de demostración")
    parser.add_argument("--demo-only", action="store_true", help="Solo ejecutar demostración")

    args = parser.parse_args()

    if args.create_demo:
        crear_datos_demo()
    elif args.demo_only:
        demo_mejoras_precio_suscripcion()
    else:
        crear_datos_demo()
        demo_mejoras_precio_suscripcion()
