#!/usr/bin/env python
"""
Script de debug para verificar por qué no aparecen vehículos en el formulario de documentos
"""

import os
import sys

import django

# Configurar Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.documentos.forms import DocumentoForm
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo


def debug_vehiculos_form():
    """Debug del formulario de documentos - vehículos"""

    print("🔍 DEBUG - FORMULARIO DOCUMENTOS - VEHÍCULOS")
    print("=" * 60)

    # Obtener usuario testuser_usa
    try:
        user = User.objects.get(username="testuser_usa")
        print(f"✅ Usuario encontrado: {user.username}")
    except User.DoesNotExist:
        print("❌ Usuario testuser_usa no encontrado")
        return

    # Obtener empresa del usuario
    try:
        empresa = user.empresa
        print(f"✅ Empresa del usuario: {empresa.nombre_taller} (ID: {empresa.id})")
        print(f"   País: {empresa.pais}")
    except AttributeError:
        print("❌ Usuario no tiene empresa asociada")
        return

    print("\n📋 CLIENTES EN LA EMPRESA")
    print("-" * 40)
    clientes = Cliente.objects.filter(empresa=empresa)
    print(f"Total clientes: {clientes.count()}")
    for cliente in clientes:
        print(f"  - {cliente.nombre} {cliente.apellido} (ID: {cliente.id})")

    print("\n🚗 VEHÍCULOS EN LA EMPRESA")
    print("-" * 40)
    vehiculos = Vehiculo.objects.filter(cliente__empresa=empresa)
    print(f"Total vehículos: {vehiculos.count()}")
    for vehiculo in vehiculos:
        print(
            f"  - {vehiculo.patente} - {vehiculo.marca} {vehiculo.modelo} (Cliente: {vehiculo.cliente.nombre} {vehiculo.cliente.apellido})"
        )

    print("\n📝 FORMULARIO - QUERYSET DE VEHÍCULOS")
    print("-" * 40)

    # Crear formulario como lo hace la vista
    form = DocumentoForm(user=user)
    vehiculo_queryset = form.fields["vehiculo"].queryset
    print(
        f"Queryset de vehículos en el formulario: {vehiculo_queryset.count()} elementos"
    )

    for vehiculo in vehiculo_queryset:
        print(f"  - {vehiculo.patente} - {vehiculo.marca} {vehiculo.modelo}")

    print("\n🔧 VERIFICACIÓN DE QUERY MANUAL")
    print("-" * 40)

    # Verificar query manual igual al del formulario
    manual_qs = Vehiculo.objects.filter(cliente__empresa=empresa)
    print(f"Query manual: {manual_qs.count()} vehículos")
    print(f"SQL Query: {manual_qs.query}")

    if vehiculo_queryset.count() == 0 and manual_qs.count() > 0:
        print(
            "🚨 PROBLEMA: El formulario no está obteniendo los vehículos correctamente"
        )
    elif vehiculo_queryset.count() == manual_qs.count():
        print("✅ El formulario obtiene los vehículos correctamente")
    else:
        print(
            f"⚠️ Diferencia: Formulario {vehiculo_queryset.count()} vs Manual {manual_qs.count()}"
        )


if __name__ == "__main__":
    debug_vehiculos_form()
