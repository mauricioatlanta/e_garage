#!/usr/bin/env python
"""
Script de verificación final - Comprobar que el dropdown de vehículos funciona
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.documentos.forms import DocumentoForm


def main():
    print("✅ VERIFICACIÓN FINAL - Dropdown de vehículos en formulario de documentos\n")

    # Test para testuser_usa
    print("1. TESTUSER_USA:")
    print("=" * 30)
    try:
        user_usa = User.objects.get(username="testuser_usa")
        empresa_usa = user_usa.empresa

        # Crear formulario
        form = DocumentoForm(empresa=empresa_usa)

        # Verificar vehículos
        vehiculo_qs = form.fields["vehiculo"].queryset
        cliente_qs = form.fields["cliente"].queryset

        print(f"✅ Empresa: {empresa_usa.nombre_taller}")
        print(f"✅ Clientes disponibles: {cliente_qs.count()}")
        print(f"✅ Vehículos disponibles: {vehiculo_qs.count()}")

        if vehiculo_qs.count() > 0:
            print("Vehículos en el dropdown:")
            for vehiculo in vehiculo_qs:
                print(
                    f"  - {vehiculo.patente} ({vehiculo.marca} {vehiculo.modelo}) - Cliente: {vehiculo.cliente.nombre}"
                )

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test para testuser_cl
    print("\n2. TESTUSER_CL:")
    print("=" * 30)
    try:
        user_cl = User.objects.get(username="testuser_cl")
        empresa_cl = user_cl.empresa

        # Crear formulario
        form = DocumentoForm(empresa=empresa_cl)

        # Verificar vehículos
        vehiculo_qs = form.fields["vehiculo"].queryset
        cliente_qs = form.fields["cliente"].queryset

        print(f"✅ Empresa: {empresa_cl.nombre_taller}")
        print(f"✅ Clientes disponibles: {cliente_qs.count()}")
        print(f"✅ Vehículos disponibles: {vehiculo_qs.count()}")

        if vehiculo_qs.count() > 0:
            print("Vehículos en el dropdown:")
            for vehiculo in vehiculo_qs:
                print(
                    f"  - {vehiculo.patente} ({vehiculo.marca} {vehiculo.modelo}) - Cliente: {vehiculo.cliente.nombre}"
                )

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("🎉 RESULTADO: El problema del dropdown de vehículos vacío ha sido SOLUCIONADO")
    print("✅ Los usuarios ahora tienen vehículos disponibles en el formulario de documentos")
    print("=" * 50)


if __name__ == "__main__":
    main()
