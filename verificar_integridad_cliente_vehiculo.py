#!/usr/bin/env python
"""
Script de verificación de integridad Cliente ↔ Vehículo ↔ Empresa

Este script implementa el checklist express que sugieres para diagnosticar
el problema de "lista vacía de vehículos en USA".
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db.models import F

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo


def verificar_integridad_datos():
    """Verifica la integridad de datos Cliente ↔ Vehículo ↔ Empresa"""

    print("🔍 VERIFICACIÓN DE INTEGRIDAD DE DATOS")
    print("=" * 60)

    # 1. Verificar clientes por país
    print("\n1️⃣ CLIENTES POR PAÍS:")
    for pais in ["CL", "US"]:
        clientes_pais = Cliente.objects.filter(empresa__pais=pais)
        print(f"   {pais}: {clientes_pais.count()} clientes")

        # Mostrar algunos ejemplos
        for cliente in clientes_pais[:3]:
            print(f"     - {cliente.nombre} {cliente.apellido} (ID: {cliente.id})")

    # 2. Verificar vehículos por país
    print("\n2️⃣ VEHÍCULOS POR PAÍS:")
    for pais in ["CL", "US"]:
        vehiculos_pais = Vehiculo.objects.filter(empresa__pais=pais)
        print(f"   {pais}: {vehiculos_pais.count()} vehículos")

        # Mostrar algunos ejemplos
        for vehiculo in vehiculos_pais[:3]:
            print(
                f"     - {vehiculo.patente} (Cliente: {vehiculo.cliente}, Empresa: {vehiculo.empresa})"
            )

    # 3. Verificar inconsistencias Cliente-Vehículo-Empresa
    print("\n3️⃣ INCONSISTENCIAS CLIENTE-VEHÍCULO-EMPRESA:")

    # Vehículos con cliente de diferente empresa
    vehiculos_empresa_inconsistente = Vehiculo.objects.exclude(
        empresa=F("cliente__empresa")
    )
    if vehiculos_empresa_inconsistente.exists():
        print(
            f"   ❌ {vehiculos_empresa_inconsistente.count()} vehículos con empresa diferente a la del cliente"
        )
        for v in vehiculos_empresa_inconsistente[:5]:
            print(f"     - Vehículo {v.id} ({v.patente})")
            print(f"       Vehículo empresa: {v.empresa}")
            print(f"       Cliente empresa: {v.cliente.empresa}")
    else:
        print("   ✅ Todos los vehículos tienen empresa consistente con su cliente")

    # 4. Test específico para USA (como en tu checklist)
    print("\n4️⃣ TEST ESPECÍFICO PARA USA:")

    # Obtener un cliente USA
    cliente_usa = Cliente.objects.filter(empresa__pais="US").first()
    if cliente_usa:
        print(f"   Cliente USA de prueba: {cliente_usa} (ID: {cliente_usa.id})")

        # Test 1: Vehículos del cliente (sin filtro de empresa)
        vehiculos_cliente_total = Vehiculo.objects.filter(cliente=cliente_usa).count()
        print(
            f"   Vehículos del cliente (sin filtro empresa): {vehiculos_cliente_total}"
        )

        # Test 2: Vehículos del cliente con filtro de empresa (como usa el endpoint)
        vehiculos_cliente_empresa = Vehiculo.objects.filter(
            cliente=cliente_usa, empresa=cliente_usa.empresa
        ).count()
        print(
            f"   Vehículos del cliente (con filtro empresa): {vehiculos_cliente_empresa}"
        )

        if vehiculos_cliente_total > vehiculos_cliente_empresa:
            print(
                f"   ⚠️ DIFERENCIA DETECTADA: {vehiculos_cliente_total - vehiculos_cliente_empresa} vehículos están en otra empresa"
            )

            # Mostrar los vehículos problemáticos
            vehiculos_problema = Vehiculo.objects.filter(cliente=cliente_usa).exclude(
                empresa=cliente_usa.empresa
            )
            for v in vehiculos_problema:
                print(
                    f"     - Vehículo {v.id} ({v.patente}): empresa={v.empresa}, cliente_empresa={cliente_usa.empresa}"
                )
        else:
            print("   ✅ No hay inconsistencias detectadas")
    else:
        print("   ⚠️ No hay clientes USA para probar")

    # 5. Verificar documentos con inconsistencias
    print("\n5️⃣ DOCUMENTOS CON INCONSISTENCIAS:")

    documentos_problematicos = []
    for doc in Documento.objects.select_related("cliente", "vehiculo", "empresa"):
        has_issue = False

        # Cliente no pertenece a la empresa del documento
        if doc.cliente and doc.empresa and doc.cliente.empresa != doc.empresa:
            has_issue = True

        # Vehículo no pertenece a la empresa del documento
        if doc.vehiculo and doc.empresa and doc.vehiculo.empresa != doc.empresa:
            has_issue = True

        # Vehículo no pertenece al cliente del documento
        if doc.vehiculo and doc.cliente and doc.vehiculo.cliente != doc.cliente:
            has_issue = True

        if has_issue:
            documentos_problematicos.append(doc)

    if documentos_problematicos:
        print(f"   ❌ {len(documentos_problematicos)} documentos con inconsistencias")
        for doc in documentos_problematicos[:3]:
            print(f"     - Documento {doc.id}: {doc.tipo} #{doc.numero}")
            print(f"       Empresa: {doc.empresa}")
            print(
                f"       Cliente: {doc.cliente} (empresa: {doc.cliente.empresa if doc.cliente else 'N/A'})"
            )
            print(
                f"       Vehículo: {doc.vehiculo} (empresa: {doc.vehiculo.empresa if doc.vehiculo else 'N/A'})"
            )
    else:
        print("   ✅ No se encontraron documentos con inconsistencias")

    # 6. Resumen y recomendaciones
    print("\n6️⃣ RESUMEN Y RECOMENDACIONES:")

    total_inconsistencias = vehiculos_empresa_inconsistente.count() + len(
        documentos_problematicos
    )

    if total_inconsistencias > 0:
        print(f"   🚨 SE ENCONTRARON {total_inconsistencias} INCONSISTENCIAS")
        print("   💡 Recomendaciones:")
        print("      1. Ejecutar script de corrección de datos")
        print("      2. Verificar que el endpoint AJAX filtre por empresa")
        print("      3. Validar que las URLs country-aware funcionen correctamente")
    else:
        print("   ✅ NO SE ENCONTRARON INCONSISTENCIAS")
        print("   💡 Si el problema persiste, verificar:")
        print("      1. URLs country-aware en el frontend")
        print("      2. JavaScript que llama al endpoint")
        print("      3. Parámetros enviados (cliente_id vs cliente)")


def test_endpoint_simulation():
    """Simula el comportamiento del endpoint AJAX"""

    print("\n🔧 SIMULACIÓN DEL ENDPOINT AJAX")
    print("=" * 60)

    # Simular diferentes escenarios
    for pais in ["CL", "US"]:
        print(f"\n📍 PAÍS: {pais}")

        # Obtener un cliente de este país
        cliente = Cliente.objects.filter(empresa__pais=pais).first()
        if not cliente:
            print(f"   ⚠️ No hay clientes para {pais}")
            continue

        print(f"   Cliente de prueba: {cliente} (ID: {cliente.id})")

        # Simular el filtro del endpoint
        vehiculos = Vehiculo.objects.filter(
            empresa=cliente.empresa,  # Filtro crítico
            cliente_id=cliente.id,
        ).values("id", "patente", "vin")

        print(f"   Vehículos encontrados: {vehiculos.count()}")

        for v in vehiculos:
            patente = v.get("patente") or "Sin patente"
            vin = v.get("vin") or "Sin VIN"
            print(f"     - ID {v['id']}: {patente} / {vin}")

        if vehiculos.count() == 0:
            print(f"   ⚠️ PROBLEMA: No se encontraron vehículos para {pais}")
            print("   💡 Posibles causas:")
            print("      - Vehículos están en otra empresa")
            print("      - Cliente no tiene vehículos")
            print("      - Filtro de empresa es incorrecto")


def corregir_inconsistencias():
    """Corrige las inconsistencias encontradas"""

    print("\n🔧 CORRIGIENDO INCONSISTENCIAS")
    print("=" * 60)

    fixed_count = 0

    # Corregir vehículos con empresa inconsistente
    vehiculos_problema = Vehiculo.objects.exclude(empresa=F("cliente__empresa"))
    for v in vehiculos_problema:
        if v.cliente and v.cliente.empresa:
            old_empresa = v.empresa
            v.empresa = v.cliente.empresa
            v.save()
            print(
                f"   ✅ Vehículo {v.id} ({v.patente}): {old_empresa} → {v.cliente.empresa}"
            )
            fixed_count += 1

    print(f"\n📊 TOTAL CORRECCIONES APLICADAS: {fixed_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Verificar integridad Cliente-Vehículo-Empresa"
    )
    parser.add_argument(
        "--check", action="store_true", help="Solo verificar inconsistencias"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Verificar y corregir inconsistencias"
    )
    parser.add_argument(
        "--test-endpoint", action="store_true", help="Simular endpoint AJAX"
    )
    parser.add_argument(
        "--all", action="store_true", help="Ejecutar todas las verificaciones"
    )

    args = parser.parse_args()

    if not any([args.check, args.fix, args.test_endpoint, args.all]):
        print("❌ Debe especificar --check, --fix, --test-endpoint o --all")
        parser.print_help()
        sys.exit(1)

    if args.check or args.fix or args.all:
        verificar_integridad_datos()

    if args.test_endpoint or args.all:
        test_endpoint_simulation()

    if args.fix or args.all:
        corregir_inconsistencias()
