#!/usr/bin/env python
"""
Script directo para verificar el estado del aislamiento multi-tenant
"""

import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()


def main():
    print("=== VERIFICACIÓN RÁPIDA MULTI-TENANT ===")

    try:
        from django.contrib.auth.models import User

        from taller.models.clientes import Cliente
        from taller.models.vehiculos import Vehiculo

        # Verificar clientes sin empresa
        clientes_sin_empresa = Cliente.objects.filter(empresa__isnull=True).count()
        print(f"❌ Clientes sin empresa: {clientes_sin_empresa}")

        # Verificar vehículos sin empresa
        vehiculos_sin_empresa = Vehiculo.objects.filter(empresa__isnull=True).count()
        print(f"❌ Vehículos sin empresa: {vehiculos_sin_empresa}")

        # Verificar empresas existentes
        try:
            from taller.models import Empresa

            empresas = Empresa.objects.all()
            print(f"📊 Empresas registradas: {empresas.count()}")
            for empresa in empresas:
                print(f"  - {empresa.nombre} ({empresa.pais})")
        except Exception as e:
            print(f"⚠️ Error al obtener empresas: {e}")

        # Verificar usuarios sin empresa
        usuarios = User.objects.all()
        usuarios_sin_empresa = 0
        for usuario in usuarios:
            if not hasattr(usuario, "empresa") or not usuario.empresa:
                usuarios_sin_empresa += 1

        print(f"❌ Usuarios sin empresa: {usuarios_sin_empresa}/{usuarios.count()}")

        # Mostrar algunos datos de muestra
        print("\n--- DATOS DE MUESTRA ---")
        clientes_muestra = Cliente.objects.all()[:5]
        for cliente in clientes_muestra:
            empresa_nombre = (
                cliente.empresa.nombre if cliente.empresa else "SIN EMPRESA"
            )
            print(f"Cliente: {cliente.nombre} - Empresa: {empresa_nombre}")

        vehiculos_muestra = Vehiculo.objects.all()[:5]
        for vehiculo in vehiculos_muestra:
            empresa_nombre = (
                vehiculo.empresa.nombre if vehiculo.empresa else "SIN EMPRESA"
            )
            cliente_empresa = (
                vehiculo.cliente.empresa.nombre
                if vehiculo.cliente and vehiculo.cliente.empresa
                else "SIN EMPRESA"
            )
            print(
                f"Vehículo: {vehiculo.patente} - Empresa: {empresa_nombre} - Cliente Empresa: {cliente_empresa}"
            )

    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
