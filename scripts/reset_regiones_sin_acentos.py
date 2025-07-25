# -*- coding: utf-8 -*-
import os
import django
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.region_ciudad import TallerRegion, TallerCiudad

# Elimina todas las ciudades primero (por FK)
TallerCiudad.objects.all().delete()
# Elimina todas las regiones
TallerRegion.objects.all().delete()

regiones = [
    "Arica y Parinacota",
    "Tarapaca",
    "Antofagasta",
    "Atacama",
    "Coquimbo",
    "Valparaiso",
    "Metropolitana de Santiago",
    "Libertador General Bernardo O'Higgins",
    "Maule",
    "Nuble",
    "Biobio",
    "La Araucania",
    "Los Rios",
    "Los Lagos",
    "Aysen del General Carlos Ibanez del Campo",
    "Magallanes y de la Antartica Chilena"
]

for nombre in regiones:
    obj, created = TallerRegion.objects.get_or_create(nombre=nombre)
    print(f"{'Creada' if created else 'Existente'}: {nombre}")
