#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models import MarcaVehiculo, ModeloVehiculo

print("=== IDs ACTUALES DE MARCAS PARA EL FORMULARIO ===\n")

marcas = MarcaVehiculo.objects.filter(activa=True).order_by("nombre")
for marca in marcas:
    modelos_count = ModeloVehiculo.objects.filter(marca=marca, activo=True).count()
    print(f"ID {marca.pk}: {marca.nombre} ({modelos_count} modelos)")

    # Mostrar algunos modelos para las marcas principales
    if marca.nombre in ["Ford", "Chevrolet", "Toyota", "Honda"]:
        modelos = ModeloVehiculo.objects.filter(marca=marca, activo=True)[:3]
        for modelo in modelos:
            print(f"    - {modelo.nombre}")
        if modelos_count > 3:
            print(f"    ... y {modelos_count - 3} más")

print("\n=== URLs PARA TESTING EN NAVEGADOR ===")
ford = MarcaVehiculo.objects.get(nombre="Ford")
chevrolet = MarcaVehiculo.objects.get(nombre="Chevrolet")
toyota = MarcaVehiculo.objects.get(nombre="Toyota")
honda = MarcaVehiculo.objects.get(nombre="Honda")

print(f"Ford (ID {ford.pk}): http://127.0.0.1:8000/api/modelos/{ford.pk}/")
print(f"Chevrolet (ID {chevrolet.pk}): http://127.0.0.1:8000/api/modelos/{chevrolet.pk}/")
print(f"Toyota (ID {toyota.pk}): http://127.0.0.1:8000/api/modelos/{toyota.pk}/")
print(f"Honda (ID {honda.pk}): http://127.0.0.1:8000/api/modelos/{honda.pk}/")
