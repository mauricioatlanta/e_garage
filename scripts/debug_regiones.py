#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.region_ciudad import TallerCiudad, TallerRegion

print("🔍 Verificando datos de región y ciudad...")
print(f"Regiones en BD: {TallerRegion.objects.count()}")
print(f"Ciudades en BD: {TallerCiudad.objects.count()}")

if TallerRegion.objects.exists():
    primera_region = TallerRegion.objects.first()
    print(f"Primera región: {primera_region} (ID: {primera_region.id})")
    ciudades_primera = TallerCiudad.objects.filter(region=primera_region)
    print(f"Ciudades en primera región: {ciudades_primera.count()}")
else:
    print("❌ No hay regiones en la base de datos")

# Verificar también las regiones usando utils.pais
from utils.pais import get_regiones

regiones_utils = get_regiones('CL')
print(f"Regiones desde utils.pais: {len(regiones_utils)}")
if regiones_utils:
    print(f"Primera región utils: {regiones_utils[0]}")
