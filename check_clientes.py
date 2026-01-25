#!/usr/bin/env python
"""
Script para verificar el conteo de clientes en la base de datos
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa

print("=" * 60)
print("VERIFICACIÓN DE CLIENTES EN BASE DE DATOS")
print("=" * 60)

# Conteo total
total = Cliente.objects.count()
print(f"\n📊 Total de clientes en la base de datos: {total}")

# Conteo por empresa
print("\n📋 Clientes por empresa:")
empresas = Empresa.objects.all()[:10]  # Primeras 10 empresas
for empresa in empresas:
    count = Cliente.objects.filter(empresa=empresa).count()
    print(f"  - {empresa.nombre_taller or empresa.id}: {count} clientes")

# Primeros 3 clientes (si existen)
if total > 0:
    print("\n👥 Primeros 3 clientes:")
    for cliente in Cliente.objects.all()[:3]:
        empresa_nombre = cliente.empresa.nombre_taller if cliente.empresa else "Sin empresa"
        print(
            f"  - ID: {cliente.id}, Nombre: {cliente.nombre} {cliente.apellido or ''}, Empresa: {empresa_nombre}"
        )
else:
    print("\n⚠️  No hay clientes en la base de datos")

print("\n" + "=" * 60)
