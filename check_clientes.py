#!/usr/bin/env python
import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models import Empresa
from taller.models.clientes import Cliente

print("🔍 Verificando clientes en la base de datos...")
print(f"Total clientes: {Cliente.objects.count()}")

if Cliente.objects.count() > 0:
    print("\n📋 Primeros 5 clientes:")
    for cliente in Cliente.objects.select_related("empresa")[:5]:
        empresa_nombre = (
            cliente.empresa.nombre_taller if cliente.empresa else "Sin empresa"
        )
        print(
            f"- {cliente.nombre} (Tax ID: {cliente.tax_id}) - Empresa: {empresa_nombre}"
        )

print(f"\n🏢 Total empresas: {Empresa.objects.count()}")
if Empresa.objects.count() > 0:
    print("Empresas disponibles:")
    for empresa in Empresa.objects.all()[:3]:
        clientes_count = Cliente.objects.filter(empresa=empresa).count()
        print(f"- {empresa.nombre_taller} (Clientes: {clientes_count})")

# Verificar si hay clientes para la empresa de Chile (CL)
empresas_chile = Empresa.objects.filter(pais="CL")
print(f"\n🇨🇱 Empresas en Chile: {empresas_chile.count()}")
for empresa in empresas_chile:
    clientes_chile = Cliente.objects.filter(empresa=empresa).count()
    print(f"- {empresa.nombre_taller}: {clientes_chile} clientes")
