#!/usr/bin/env python
"""
Script para limpiar cuentas de suscripción de prueba en eGarage.
- Mantiene solo una cuenta por país que tenga datos
- Mantiene la cuenta de administrador
- Borra todas las demás cuentas sin datos

Uso:
    python tools/limpiar_cuentas_prueba.py
    python tools/limpiar_cuentas_prueba.py --yes  # Ejecución automática sin confirmación
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.db import transaction

from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento
from taller.models.catalogo_repuestos import Part
from taller.models.catalogo_servicios import Service
from taller.models.repuesto import Repuesto


def tiene_datos(empresa):
    """Verifica si una empresa tiene datos de prueba"""
    # Verificar clientes
    if Cliente.objects.filter(empresa=empresa).exists():
        return True

    # Verificar vehículos
    if Vehiculo.objects.filter(empresa=empresa).exists():
        return True

    # Verificar documentos
    if Documento.objects.filter(empresa=empresa).exists():
        return True

    # Verificar repuestos (Part - nuevo modelo con I18N)
    if Part.objects.filter(empresa=empresa).exists():
        return True

    # Verificar repuestos (Repuesto - modelo legacy)
    if Repuesto.objects.filter(empresa=empresa).exists():
        return True

    # Verificar servicios (Service)
    if Service.objects.filter(empresa=empresa).exists():
        return True

    return False


def contar_datos(empresa):
    """Cuenta cuántos datos tiene una empresa"""
    return {
        "clientes": Cliente.objects.filter(empresa=empresa).count(),
        "vehiculos": Vehiculo.objects.filter(empresa=empresa).count(),
        "documentos": Documento.objects.filter(empresa=empresa).count(),
        "repuestos_part": Part.objects.filter(empresa=empresa).count(),
        "repuestos_legacy": Repuesto.objects.filter(empresa=empresa).count(),
        "servicios": Service.objects.filter(empresa=empresa).count(),
    }


def main():
    # Verificar si se pasó el flag --yes
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv

    print("=" * 80)
    print("LIMPIEZA DE CUENTAS DE PRUEBA - eGarage")
    print("=" * 80)
    print()

    # Obtener todas las empresas con plan trial
    empresas_trial = Empresa.objects.filter(plan="trial").select_related("user")

    print(f"Total de empresas con plan trial: {empresas_trial.count()}")
    print()

    # Separar por país y verificar datos
    empresas_por_pais = {}
    empresas_con_datos = {}
    empresas_sin_datos = []

    for empresa in empresas_trial:
        pais = empresa.pais
        if pais not in empresas_por_pais:
            empresas_por_pais[pais] = []
        empresas_por_pais[pais].append(empresa)

        if tiene_datos(empresa):
            if pais not in empresas_con_datos:
                empresas_con_datos[pais] = []
            empresas_con_datos[pais].append(empresa)
        else:
            empresas_sin_datos.append(empresa)

    print("RESUMEN POR PAÍS:")
    print("-" * 80)
    for pais, empresas in sorted(empresas_por_pais.items()):
        print(f"\n{pais}: {len(empresas)} empresas")
        con_datos = [e for e in empresas if tiene_datos(e)]
        sin_datos = [e for e in empresas if not tiene_datos(e)]
        print(f"  - Con datos: {len(con_datos)}")
        print(f"  - Sin datos: {len(sin_datos)}")

        if con_datos:
            print(f"\n  Empresas CON DATOS:")
            for emp in con_datos:
                datos = contar_datos(emp)
                total = sum(datos.values())
                print(f"    - {emp.nombre_taller} (user: {emp.user.username})")
                print(f"      Datos: {datos} (Total: {total})")

    print("\n" + "=" * 80)
    print("EMPRESAS SIN DATOS (serán eliminadas):")
    print("-" * 80)
    for empresa in empresas_sin_datos:
        print(f"  - {empresa.nombre_taller} (user: {empresa.user.username}, país: {empresa.pais})")

    # Identificar cuentas a mantener
    empresas_a_mantener = []

    # Mantener una cuenta por país que tenga datos (la que tenga más datos)
    for pais, empresas in empresas_con_datos.items():
        if empresas:
            # Ordenar por cantidad de datos (descendente)
            empresas_ordenadas = sorted(
                empresas, key=lambda e: sum(contar_datos(e).values()), reverse=True
            )
            # Mantener la primera (la que tiene más datos)
            empresas_a_mantener.append(empresas_ordenadas[0])
            print(
                f"\n✓ Manteniendo para {pais}: {empresas_ordenadas[0].nombre_taller} (user: {empresas_ordenadas[0].user.username})"
            )

            # Las demás con datos también se eliminarán (solo una por país)
            if len(empresas_ordenadas) > 1:
                print(
                    f"  ⚠ Eliminando {len(empresas_ordenadas) - 1} empresa(s) adicional(es) con datos en {pais}"
                )

    # Mantener cuenta de administrador
    admin_users = User.objects.filter(is_superuser=True)
    for admin_user in admin_users:
        if hasattr(admin_user, "empresa"):
            if admin_user.empresa not in empresas_a_mantener:
                empresas_a_mantener.append(admin_user.empresa)
                print(f"\n✓ Manteniendo cuenta de administrador: {admin_user.username}")

    # Identificar empresas a eliminar
    empresas_a_eliminar = []
    for empresa in empresas_trial:
        if empresa not in empresas_a_mantener:
            empresas_a_eliminar.append(empresa)

    print("\n" + "=" * 80)
    print(f"RESUMEN FINAL:")
    print("-" * 80)
    print(f"Total empresas trial: {empresas_trial.count()}")
    print(f"Empresas a mantener: {len(empresas_a_mantener)}")
    print(f"Empresas a eliminar: {len(empresas_a_eliminar)}")
    print()

    if not empresas_a_eliminar:
        print("✓ No hay empresas para eliminar. Todo está limpio.")
        return

    # Confirmar antes de eliminar
    print("⚠️  ADVERTENCIA: Se eliminarán las siguientes empresas y sus usuarios:")
    print("-" * 80)
    for empresa in empresas_a_eliminar:
        datos = contar_datos(empresa)
        total = sum(datos.values())
        print(f"  - {empresa.nombre_taller}")
        print(f"    User: {empresa.user.username} ({empresa.user.email})")
        print(f"    País: {empresa.pais}")
        print(f"    Datos: {datos} (Total: {total})")

    print("\n" + "=" * 80)
    if auto_confirm:
        print("⚠️  Modo automático activado (--yes). Procediendo con la eliminación...")
        respuesta = "SI"
    else:
        respuesta = input(
            "¿Deseas continuar con la eliminación? (escribe 'SI' o 'si' para confirmar): "
        )

    if respuesta.upper() != "SI":
        print("Operación cancelada.")
        return

    # Eliminar empresas y usuarios
    print("\nEliminando empresas y usuarios...")
    eliminadas = 0

    with transaction.atomic():
        for empresa in empresas_a_eliminar:
            try:
                user = empresa.user
                nombre_empresa = empresa.nombre_taller
                username = user.username

                # Eliminar en el orden correcto debido a relaciones PROTECT
                # 1. Eliminar documentos primero (tienen PROTECT con Cliente)
                Documento.objects.filter(empresa=empresa).delete()

                # 2. Eliminar clientes (ahora que no hay documentos)
                Cliente.objects.filter(empresa=empresa).delete()

                # 3. Eliminar vehículos
                Vehiculo.objects.filter(empresa=empresa).delete()

                # 4. Eliminar repuestos
                Part.objects.filter(empresa=empresa).delete()
                Repuesto.objects.filter(empresa=empresa).delete()

                # 5. Eliminar servicios
                Service.objects.filter(empresa=empresa).delete()

                # 6. Finalmente eliminar empresa
                empresa.delete()

                # 7. Eliminar usuario si no es admin
                if not user.is_superuser:
                    user.delete()
                    print(f"  ✓ Eliminada: {nombre_empresa} (user: {username})")
                else:
                    print(f"  ⚠ Usuario admin {username} no eliminado (solo empresa)")

                eliminadas += 1
            except Exception as e:
                print(f"  ✗ Error al eliminar {empresa.nombre_taller}: {e}")
                import traceback

                traceback.print_exc()

    print("\n" + "=" * 80)
    print(f"✓ Proceso completado. {eliminadas} empresa(s) eliminada(s).")
    print("=" * 80)


if __name__ == "__main__":
    main()
