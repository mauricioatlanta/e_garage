#!/usr/bin/env python
"""
Test de unicidad condicional en PrecioSuscripcion
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db import IntegrityError

from taller.models.precio_suscripcion import PrecioSuscripcion


def test_unicidad_condicional():
    """Prueba la unicidad condicional del modelo"""

    print("🔒 TEST DE UNICIDAD CONDICIONAL")
    print("=" * 50)

    # 1. Verificar que existe un plan mensual activo para Chile
    print("\n1️⃣ Verificando plan mensual activo para Chile:")
    plan_activo = PrecioSuscripcion.objects.vigente("CL", "mensual")
    if plan_activo:
        print(f"   ✅ Existe: {plan_activo}")
        print(f"   Estado: {'Activo' if plan_activo.activo else 'Inactivo'}")
    else:
        print("   ❌ No hay plan mensual activo para Chile")
        return

    # 2. Intentar crear otro plan mensual activo para Chile (debería fallar)
    print("\n2️⃣ Intentando crear otro plan mensual activo para Chile:")
    try:
        plan_duplicado = PrecioSuscripcion.objects.create(
            tipo_plan=PrecioSuscripcion.TipoPlan.MENSUAL,
            pais=PrecioSuscripcion.Pais.CL,
            precio=30000,  # Precio diferente
            nombre_plan="Plan Mensual Duplicado",
            activo=True,  # ← Esto debería causar el error
        )
        print("   ❌ Error: Se creó un duplicado activo (no debería pasar)")
    except IntegrityError as e:
        print(f"   ✅ Unicidad funcionó: {e}")

    # 3. Crear plan mensual INACTIVO para Chile (debería funcionar)
    print("\n3️⃣ Creando plan mensual INACTIVO para Chile:")
    try:
        plan_historico = PrecioSuscripcion.objects.create(
            tipo_plan=PrecioSuscripcion.TipoPlan.MENSUAL,
            pais=PrecioSuscripcion.Pais.CL,
            precio=15000,
            nombre_plan="Plan Mensual Histórico",
            activo=False,  # ← Inactivo, debería funcionar
        )
        print(f"   ✅ Plan histórico creado: {plan_historico}")

        # Limpiar el plan de prueba
        plan_historico.delete()
        print("   🧹 Plan de prueba eliminado")

    except IntegrityError as e:
        print(f"   ❌ Error inesperado: {e}")

    # 4. Verificar que solo hay un plan activo por tipo/país
    print("\n4️⃣ Verificando unicidad en todos los planes activos:")
    planes_activos = PrecioSuscripcion.objects.activos().order_by("pais", "tipo_plan")

    combinaciones = {}
    for plan in planes_activos:
        clave = f"{plan.pais}_{plan.tipo_plan}"
        if clave in combinaciones:
            print(f"   ❌ DUPLICADO ENCONTRADO: {clave}")
            print(f"      Plan 1: {combinaciones[clave]}")
            print(f"      Plan 2: {plan}")
        else:
            combinaciones[clave] = plan

    print(f"   ✅ {len(combinaciones)} combinaciones únicas verificadas")

    # 5. Mostrar resumen de planes por país
    print("\n5️⃣ Resumen de planes por país:")
    for pais in ["CL", "US"]:
        planes_pais = PrecioSuscripcion.objects.para_pais(pais)
        activos = planes_pais.filter(activo=True).count()
        inactivos = planes_pais.filter(activo=False).count()
        print(f"   {pais}: {activos} activos, {inactivos} inactivos")

    print("\n" + "=" * 50)
    print("✅ TEST DE UNICIDAD COMPLETADO")


if __name__ == "__main__":
    test_unicidad_condicional()
