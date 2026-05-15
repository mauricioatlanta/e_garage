#!/usr/bin/env python
"""
Debug script para verificar el problema con vehículos en formulario de documentos
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import get_user_model

from taller.documentos.forms import DocumentoForm
from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo

User = get_user_model()


def main():
    print("🔍 DEBUG: Analizando problema de vehículos en formulario de documentos\n")

    # 1. Verificar usuarios y empresas
    print("1. USUARIOS Y EMPRESAS:")
    print("=" * 50)
    for user in User.objects.all():
        try:
            empresa = user.empresa
            print(
                f"Usuario: {user.username} -> Empresa: {empresa.nombre_taller} (ID: {empresa.id}, País: {empresa.pais})"
            )
        except Exception as e:
            print(f"Usuario: {user.username} -> Sin empresa asignada: {e}")

    print("\n2. CLIENTES POR EMPRESA:")
    print("=" * 50)
    for empresa in Empresa.objects.all():
        clientes = Cliente.objects.filter(empresa=empresa)
        print(f"Empresa {empresa.nombre_taller} ({empresa.pais}): {clientes.count()} clientes")
        for cliente in clientes:
            print(f"  - {cliente.nombre} {cliente.apellido}")

    print("\n3. VEHÍCULOS POR EMPRESA:")
    print("=" * 50)
    for empresa in Empresa.objects.all():
        vehiculos = Vehiculo.objects.filter(cliente__empresa=empresa)
        print(f"Empresa {empresa.nombre_taller} ({empresa.pais}): {vehiculos.count()} vehículos")
        for vehiculo in vehiculos:
            print(
                f"  - {vehiculo.patente} ({vehiculo.marca} {vehiculo.modelo}) - Cliente: {vehiculo.cliente.nombre}"
            )

    print("\n4. TESTEO DocumentoForm PARA testuser_usa:")
    print("=" * 50)
    try:
        user_usa = User.objects.get(username="testuser_usa")
        empresa_usa = user_usa.empresa
        print(f"Usuario: {user_usa.username}")
        print(f"Empresa: {empresa_usa.nombre_taller} (ID: {empresa_usa.id})")

        # Crear formulario como lo hace la vista
        form = DocumentoForm(empresa=empresa_usa)

        # Verificar queryset de vehículos
        vehiculo_qs = form.fields["vehiculo"].queryset
        print(f"Queryset de vehículos: {vehiculo_qs.count()} vehículos encontrados")

        if vehiculo_qs.count() > 0:
            print("Vehículos disponibles:")
            for vehiculo in vehiculo_qs:
                print(
                    f"  - {vehiculo.patente} ({vehiculo.marca} {vehiculo.modelo}) - Cliente: {vehiculo.cliente.nombre}"
                )
        else:
            print("❌ No hay vehículos en el queryset")

            # Verificar si hay vehículos para esa empresa
            vehiculos_empresa = Vehiculo.objects.filter(cliente__empresa=empresa_usa)
            print(f"Vehículos directos de la empresa: {vehiculos_empresa.count()}")
            for vehiculo in vehiculos_empresa:
                print(f"  - {vehiculo.patente} - Cliente: {vehiculo.cliente.nombre}")

        # Verificar queryset de clientes
        cliente_qs = form.fields["cliente"].queryset
        print(f"Queryset de clientes: {cliente_qs.count()} clientes encontrados")

    except User.DoesNotExist:
        print("❌ Usuario testuser_usa no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n5. TESTEO DocumentoForm PARA testuser_cl:")
    print("=" * 50)
    try:
        user_cl = User.objects.get(username="testuser_cl")
        empresa_cl = user_cl.empresa
        print(f"Usuario: {user_cl.username}")
        print(f"Empresa: {empresa_cl.nombre_taller} (ID: {empresa_cl.id})")

        # Crear formulario como lo hace la vista
        form = DocumentoForm(empresa=empresa_cl)

        # Verificar queryset de vehículos
        vehiculo_qs = form.fields["vehiculo"].queryset
        print(f"Queryset de vehículos: {vehiculo_qs.count()} vehículos encontrados")

        if vehiculo_qs.count() > 0:
            print("Vehículos disponibles:")
            for vehiculo in vehiculo_qs:
                print(
                    f"  - {vehiculo.patente} ({vehiculo.marca} {vehiculo.modelo}) - Cliente: {vehiculo.cliente.nombre}"
                )
        else:
            print("❌ No hay vehículos en el queryset")

        # Verificar queryset de clientes
        cliente_qs = form.fields["cliente"].queryset
        print(f"Queryset de clientes: {cliente_qs.count()} clientes encontrados")

    except User.DoesNotExist:
        print("❌ Usuario testuser_cl no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
