import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

import json
from taller.models.region_ciudad import TallerRegion, TallerCiudad

# Eliminar datos previos
print("🧹 Eliminando regiones y ciudades existentes...")
TallerCiudad.objects.all().delete()
TallerRegion.objects.all().delete()

# Cargar nuevas regiones y ciudades
print("📥 Cargando regiones y ciudades desde archivo...")
with open('regiones_ciudades.json', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    region_name = item["region"]
    region = TallerRegion.objects.create(nombre=region_name)
    for ciudad_name in item["ciudades"]:
        TallerCiudad.objects.create(nombre=ciudad_name, region=region)

print("✅ Regiones y ciudades cargadas correctamente.")
