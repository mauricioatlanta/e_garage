#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db import models

from taller.models.repuesto import Repuesto

print("=== VERIFICACIÓN DE REPUESTOS ===")
print(f"Total repuestos: {Repuesto.objects.count()}")
print("\nPrimeros 5 repuestos:")
for r in Repuesto.objects.all()[:5]:
    print(f"- ID: {r.id}")
    print(f"  Part Number: {r.part_number}")
    print(f"  Nombre: {r.nombre}")
    print(f"  Precio Compra: ${r.precio_compra}")
    print(f"  Precio Venta: ${r.precio_venta}")
    print(f"  Stock: {r.cantidad_stock}")
    print(f"  Proveedor: {r.proveedor}")
    print("---")

# Buscar repuestos que contengan "of"
print("\nRepuestos que contienen 'of':")
repuestos_of = Repuesto.objects.filter(
    models.Q(nombre__icontains="of") | models.Q(part_number__icontains="of")
)
for r in repuestos_of:
    print(f"- {r.part_number} | {r.nombre} | ${r.precio_venta}")
