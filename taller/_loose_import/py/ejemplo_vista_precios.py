#!/usr/bin/env python
"""
Vista de ejemplo que demuestra el uso del modelo PrecioSuscripcion refinado

Esta vista muestra cómo usar las nuevas funcionalidades en una aplicación real.
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.shortcuts import render

from taller.models.precio_suscripcion import PrecioSuscripcion


def vista_precios_ejemplo(request):
    """
    Vista de ejemplo que demuestra el uso del modelo PrecioSuscripcion refinado
    """

    # Detectar país del usuario (similar a la vista real)
    pais_usuario = "CL"  # Default Chile
    if request.user.is_authenticated and hasattr(request.user, "empresa"):
        pais_usuario = request.user.empresa.pais
    elif request.GET.get("country"):
        pais_usuario = request.GET.get("country").upper()

    # 🚀 USANDO EL MANAGER REFINADO
    # Antes: PrecioSuscripcion.objects.filter(pais=pais_usuario, activo=True)
    # Ahora: Mucho más expresivo y limpio
    planes_activos = (
        PrecioSuscripcion.objects.activos().para_pais(pais_usuario).order_by("precio")
    )

    # Obtener plan específico vigente
    plan_mensual_vigente = PrecioSuscripcion.get_vigente(pais_usuario, "mensual")

    # Obtener todos los planes para mostrar comparación
    todos_los_planes = PrecioSuscripcion.objects.para_pais(pais_usuario).order_by(
        "tipo_plan", "-activo"
    )

    # Estadísticas para el contexto
    total_planes = PrecioSuscripcion.objects.count()
    planes_activos_total = PrecioSuscripcion.objects.activos().count()

    context = {
        "planes": planes_activos,
        "plan_mensual_vigente": plan_mensual_vigente,
        "todos_los_planes": todos_los_planes,
        "pais_usuario": pais_usuario,
        "total_planes": total_planes,
        "planes_activos_total": planes_activos_total,
        "empresa": (
            getattr(request.user, "empresa", None)
            if request.user.is_authenticated
            else None
        ),
    }

    return render(request, "ejemplo_precios_suscripcion.html", context)


def demo_uso_api():
    """
    Demuestra el uso de la API del modelo refinado
    """

    print("🚀 DEMO DE USO DE API REFINADA")
    print("=" * 50)

    # 1. Obtener planes activos para Chile
    print("\n1️⃣ Planes activos para Chile:")
    planes_chile = PrecioSuscripcion.objects.activos().para_pais("CL")
    for plan in planes_chile:
        print(f"   - {plan.get_tipo_plan_display()}: {plan.precio_formateado()}")

    # 2. Obtener plan vigente específico
    print("\n2️⃣ Plan mensual vigente en USA:")
    plan_usa_mensual = PrecioSuscripcion.get_vigente("US", "mensual")
    if plan_usa_mensual:
        print(f"   {plan_usa_mensual}")
        print(
            f"   Características: {', '.join(plan_usa_mensual.caracteristicas_list())}"
        )
    else:
        print("   No hay plan mensual vigente en USA")

    # 3. Comparar precios entre países
    print("\n3️⃣ Comparación de precios mensuales:")
    for pais in ["CL", "US"]:
        plan_mensual = PrecioSuscripcion.get_vigente(pais, "mensual")
        if plan_mensual:
            print(f"   {pais}: {plan_mensual.precio_formateado()}")

    # 4. Mostrar histórico (planes inactivos)
    print("\n4️⃣ Histórico de precios (planes inactivos):")
    planes_inactivos = PrecioSuscripcion.objects.filter(activo=False).order_by(
        "pais", "tipo_plan"
    )
    for plan in planes_inactivos:
        print(
            f"   {plan.get_pais_display()} - {plan.get_tipo_plan_display()}: {plan.precio_formateado()} (Histórico)"
        )

    # 5. Estadísticas generales
    print("\n5️⃣ Estadísticas:")
    print(f"   Total de planes: {PrecioSuscripcion.objects.count()}")
    print(f"   Planes activos: {PrecioSuscripcion.objects.activos().count()}")
    print(f"   Planes para Chile: {PrecioSuscripcion.objects.para_pais('CL').count()}")
    print(f"   Planes para USA: {PrecioSuscripcion.objects.para_pais('US').count()}")


def demo_validaciones():
    """
    Demuestra las validaciones del modelo
    """

    print("\n🔒 DEMO DE VALIDACIONES")
    print("=" * 50)

    from django.core.exceptions import ValidationError

    # Intentar crear un plan con precio negativo
    print("\n1️⃣ Intentando crear plan con precio negativo:")
    try:
        plan_invalido = PrecioSuscripcion(
            tipo_plan=PrecioSuscripcion.TipoPlan.MENSUAL,
            pais=PrecioSuscripcion.Pais.CL,
            precio=-100,  # Precio negativo
            usuarios_incluidos=5,
        )
        plan_invalido.clean()
        print("   ❌ Error: La validación debería haber fallado")
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e}")

    # Intentar crear un plan con 0 usuarios
    print("\n2️⃣ Intentando crear plan con 0 usuarios:")
    try:
        plan_invalido = PrecioSuscripcion(
            tipo_plan=PrecioSuscripcion.TipoPlan.MENSUAL,
            pais=PrecioSuscripcion.Pais.CL,
            precio=25000,
            usuarios_incluidos=0,  # 0 usuarios
        )
        plan_invalido.clean()
        print("   ❌ Error: La validación debería haber fallado")
    except ValidationError as e:
        print(f"   ✅ Validación funcionó: {e}")

    # Crear plan con moneda incorrecta (debería normalizarse)
    print("\n3️⃣ Creando plan con moneda incorrecta (debería normalizarse):")
    plan_normalizado = PrecioSuscripcion(
        tipo_plan=PrecioSuscripcion.TipoPlan.MENSUAL,
        pais=PrecioSuscripcion.Pais.CL,
        precio=25000,
        moneda="USD",  # Incorrecta para Chile
    )
    plan_normalizado.clean()
    print(f"   ✅ Moneda normalizada: {plan_normalizado.moneda}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Demo de uso de PrecioSuscripcion refinado"
    )
    parser.add_argument("--api", action="store_true", help="Demo de uso de API")
    parser.add_argument(
        "--validaciones", action="store_true", help="Demo de validaciones"
    )
    parser.add_argument("--todo", action="store_true", help="Ejecutar todas las demos")

    args = parser.parse_args()

    if args.api or args.todo:
        demo_uso_api()

    if args.validaciones or args.todo:
        demo_validaciones()

    if not any([args.api, args.validaciones, args.todo]):
        print("Ejecuta con --api, --validaciones, o --todo")
        parser.print_help()
