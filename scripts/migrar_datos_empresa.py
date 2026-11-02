#!/usr/bin/env python
"""
Script para migrar datos existentes sin empresa asignada
a la primera empresa disponible o crear una empresa por defecto.
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo


def migrar_datos():
    print("🔄 Iniciando migración de datos...")

    # 1. Obtener o crear una empresa por defecto
    primera_empresa = Empresa.objects.first()
    if not primera_empresa:
        # Crear empresa por defecto
        primer_usuario = User.objects.first()
        if primer_usuario:
            primera_empresa = Empresa.objects.create(
                usuario=primer_usuario,
                nombre_taller="Taller Principal",
                empresa="Empresa Principal",
            )
            print(f"✅ Empresa por defecto creada: {primera_empresa}")
        else:
            print("❌ No hay usuarios en el sistema. Crear un usuario primero.")
            return
    else:
        print(f"✅ Usando empresa existente: {primera_empresa}")

    # 2. Migrar clientes sin empresa
    clientes_sin_empresa = Cliente.objects.filter(empresa__isnull=True)
    count_clientes = clientes_sin_empresa.count()
    if count_clientes > 0:
        clientes_sin_empresa.update(empresa=primera_empresa)
        print(f"✅ Migrados {count_clientes} clientes a la empresa {primera_empresa}")
    else:
        print("✅ Todos los clientes ya tienen empresa asignada")

    # 3. Migrar vehículos sin empresa
    vehiculos_sin_empresa = Vehiculo.objects.filter(empresa__isnull=True)
    count_vehiculos = vehiculos_sin_empresa.count()
    if count_vehiculos > 0:
        vehiculos_sin_empresa.update(empresa=primera_empresa)
        print(f"✅ Migrados {count_vehiculos} vehículos a la empresa {primera_empresa}")
    else:
        print("✅ Todos los vehículos ya tienen empresa asignada")

    print("🎉 Migración completada exitosamente!")


if __name__ == "__main__":
    migrar_datos()
