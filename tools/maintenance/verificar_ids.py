#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models import MarcaVehiculo, ModeloVehiculo

print('=== IDs DE MARCAS ===')
marcas = MarcaVehiculo.objects.filter(activa=True).order_by('id')
for marca in marcas:
    modelos_count = ModeloVehiculo.objects.filter(marca=marca, activo=True).count()
    print(f'ID {marca.id}: {marca.nombre} ({modelos_count} modelos)')

print('\n=== MODELOS DE AUDI ===')
try:
    audi = MarcaVehiculo.objects.get(nombre='Audi')
    modelos_audi = ModeloVehiculo.objects.filter(marca=audi, activo=True)
    print(f'Audi ID: {audi.id}')
    print(f'Modelos de Audi:')
    for modelo in modelos_audi:
        print(f'  - {modelo.nombre} (ID: {modelo.id})')
except MarcaVehiculo.DoesNotExist:
    print('Audi no encontrada')
