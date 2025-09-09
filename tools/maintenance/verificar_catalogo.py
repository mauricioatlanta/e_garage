#!/usr/bin/env python
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.db.models import Count

from taller.models.catalogo import CatalogoModeloAuto

# Verificar total
total = CatalogoModeloAuto.objects.count()
print(f'📊 Total de modelos: {total}')

# Marcas más populares
marcas = CatalogoModeloAuto.objects.values('marca').annotate(
    total=Count('modelo')
).order_by('-total')[:10]

print('\n🏆 Top 10 marcas con más modelos:')
for marca in marcas:
    print(f"  {marca['marca']}: {marca['total']} modelos")

# Algunos ejemplos
print('\n🚗 Ejemplos de modelos Ford:')
ford_models = CatalogoModeloAuto.objects.filter(marca='Ford')[:5]
for model in ford_models:
    print(f"  - {model.modelo}")

print('\n🚗 Ejemplos de modelos Toyota:')
toyota_models = CatalogoModeloAuto.objects.filter(marca='Toyota')[:5]
for model in toyota_models:
    print(f"  - {model.modelo}")

print('\n✅ Verificación completada')
