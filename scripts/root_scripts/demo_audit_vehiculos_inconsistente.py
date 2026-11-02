#!/usr/bin/env python
"""
Demo del management command audit_vehiculos con datos inconsistentes

Este script simula cómo funcionaría el comando cuando hay inconsistencias.
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo


def demo_inconsistencias():
    """Simula escenarios de inconsistencias para demostrar el comando"""

    print("🎭 DEMO: MANAGEMENT COMMAND AUDIT_VEHICULOS")
    print("=" * 60)

    # Obtener empresas y clientes existentes
    empresa_chile = Empresa.objects.filter(pais="CL").first()
    empresa_usa = Empresa.objects.filter(pais="US").first()

    cliente_chile = Cliente.objects.filter(empresa=empresa_chile).first()
    cliente_usa = Cliente.objects.filter(empresa=empresa_usa).first()

    if not all([empresa_chile, empresa_usa, cliente_chile, cliente_usa]):
        print("❌ No se encontraron datos suficientes para la demo")
        return

    print("📋 DATOS DE PRUEBA:")
    print(f"   Empresa Chile: {empresa_chile}")
    print(f"   Empresa USA: {empresa_usa}")
    print(f"   Cliente Chile: {cliente_chile}")
    print(f"   Cliente USA: {cliente_usa}")

    # Crear un vehículo con inconsistencia
    print("\n🔧 CREANDO VEHÍCULO CON INCONSISTENCIA...")

    # Buscar un vehículo existente para modificar
    vehiculo_test = Vehiculo.objects.first()
    if not vehiculo_test:
        print("❌ No hay vehículos para modificar")
        return

    # Guardar estado original
    empresa_original = vehiculo_test.empresa
    cliente_original = vehiculo_test.cliente

    # Crear inconsistencia: vehículo de Chile asignado a empresa USA
    vehiculo_test.empresa = empresa_usa
    vehiculo_test.save()

    print(f"   Vehículo {vehiculo_test.id} ({vehiculo_test.patente})")
    print(f"   Cliente: {vehiculo_test.cliente} (empresa: {vehiculo_test.cliente.empresa})")
    print(f"   Vehículo empresa: {vehiculo_test.empresa}")
    print("   ⚠️ INCONSISTENCIA CREADA: cliente.empresa ≠ vehiculo.empresa")

    # Ejecutar el comando de auditoría
    print("\n🔍 EJECUTANDO AUDITORÍA...")
    print("=" * 60)

    # Simular la ejecución del comando
    from io import StringIO

    from django.core.management import call_command

    # Capturar salida
    out = StringIO()
    call_command("audit_vehiculos", stdout=out)
    output = out.getvalue()

    print(output)

    # Mostrar opciones de corrección
    print("\n🔧 OPCIONES DE CORRECCIÓN:")
    print("   1. Corrección automática:")
    print("      python manage.py audit_vehiculos --fix")
    print("   2. Ver detalles:")
    print("      python manage.py audit_vehiculos --verbose")

    # Restaurar estado original
    print("\n🔄 RESTAURANDO ESTADO ORIGINAL...")
    vehiculo_test.empresa = empresa_original
    vehiculo_test.save()
    print(f"   ✅ Vehículo restaurado a empresa original: {empresa_original}")


def mostrar_ayuda_comando():
    """Muestra la ayuda del comando"""

    print("\n📖 AYUDA DEL COMANDO:")
    print("=" * 60)

    from io import StringIO

    from django.core.management import call_command

    # Capturar ayuda
    out = StringIO()
    try:
        call_command("audit_vehiculos", "--help", stdout=out)
        print(out.getvalue())
    except Exception as e:
        print(f"Error obteniendo ayuda: {e}")


if __name__ == "__main__":
    demo_inconsistencias()
    mostrar_ayuda_comando()
