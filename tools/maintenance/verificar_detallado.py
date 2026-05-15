#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models import MarcaVehiculo, ModeloVehiculo

print("=== VERIFICACIÓN DETALLADA DE MARCAS Y MODELOS ===\n")

marcas = MarcaVehiculo.objects.filter(activa=True).order_by("nombre")
total_marcas = marcas.count()
marcas_sin_modelos = 0

for marca in marcas:
    modelos = ModeloVehiculo.objects.filter(marca=marca, activo=True).order_by("nombre")
    modelos_count = modelos.count()

    if modelos_count == 0:
        marcas_sin_modelos += 1
        print(f"❌ {marca.nombre}: {modelos_count} modelos")
    else:
        print(f"✅ {marca.nombre}: {modelos_count} modelos")
        for modelo in modelos:
            print(
                f"   - {modelo.nombre} ({modelo.tipo_vehiculo}, {modelo.anio_inicio}-{modelo.anio_fin or 'actual'})"
            )
    print()

print("📊 RESUMEN:")
print(f"Total marcas: {total_marcas}")
print(f"Marcas sin modelos: {marcas_sin_modelos}")
print(f"Marcas con modelos: {total_marcas - marcas_sin_modelos}")

# Verificar algunos modelos específicos sospechosos
print("\n🔍 VERIFICACIÓN DE MODELOS ESPECÍFICOS:")
problematicos = ["Camry", "Corolla", "Civic", "Accord"]
for nombre_modelo in problematicos:
    modelos = ModeloVehiculo.objects.filter(nombre__icontains=nombre_modelo, activo=True)
    if modelos.exists():
        for modelo in modelos:
            print(f"- {modelo.nombre} está asignado a: {modelo.marca.nombre}")
    else:
        print(f"- {nombre_modelo}: No encontrado")
