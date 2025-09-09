#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models import MarcaVehiculo, ModeloVehiculo

print('=== VERIFICACIÓN ESPECÍFICA: FORD Y CHEVROLET ===\n')

# Verificar Ford
try:
    ford = MarcaVehiculo.objects.get(nombre='Ford', activa=True)
    print(f"✅ Ford encontrada - ID: {ford.pk}")
    modelos_ford = ModeloVehiculo.objects.filter(marca=ford, activo=True)
    print(f"Modelos Ford en BD: {modelos_ford.count()}")
    for modelo in modelos_ford:
        print(f"  - {modelo.nombre} (ID: {modelo.pk}, activo: {modelo.activo})")
except MarcaVehiculo.DoesNotExist:
    print("❌ Ford no encontrada")

print()

# Verificar Chevrolet  
try:
    chevrolet = MarcaVehiculo.objects.get(nombre='Chevrolet', activa=True)
    print(f"✅ Chevrolet encontrada - ID: {chevrolet.pk}")
    modelos_chevrolet = ModeloVehiculo.objects.filter(marca=chevrolet, activo=True)
    print(f"Modelos Chevrolet en BD: {modelos_chevrolet.count()}")
    for modelo in modelos_chevrolet:
        print(f"  - {modelo.nombre} (ID: {modelo.pk}, activo: {modelo.activo})")
except MarcaVehiculo.DoesNotExist:
    print("❌ Chevrolet no encontrada")

print(f"\n=== IDs DE TODAS LAS MARCAS ===")
marcas = MarcaVehiculo.objects.filter(activa=True).order_by('nombre')
for marca in marcas[:10]:  # Solo primeras 10 para no saturar
    print(f"ID {marca.pk}: {marca.nombre}")

print(f"\n=== VERIFICAR CAMPO ACTIVO EN MODELOS ===")
# Verificar si hay modelos inactivos
total_modelos = ModeloVehiculo.objects.count()
modelos_activos = ModeloVehiculo.objects.filter(activo=True).count()
modelos_inactivos = ModeloVehiculo.objects.filter(activo=False).count()

print(f"Total modelos: {total_modelos}")
print(f"Modelos activos: {modelos_activos}")
print(f"Modelos inactivos: {modelos_inactivos}")

if modelos_inactivos > 0:
    print("Modelos inactivos encontrados:")
    inactivos = ModeloVehiculo.objects.filter(activo=False)[:5]
    for modelo in inactivos:
        print(f"  - {modelo.marca.nombre} {modelo.nombre} (activo: {modelo.activo})")
