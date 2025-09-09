#!/usr/bin/env python3

import os
import sys

import django

# Configurar Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from vehiculos.models import Marca, Modelo

print("=== VERIFICACIÓN DE DATOS CHILE ===")

# Verificar marcas
marcas_chile = Marca.objects.filter(pais="CL")
print(f"\n📊 Total marcas Chile: {marcas_chile.count()}")

if marcas_chile.exists():
    print("\n🔍 Primeras 5 marcas:")
    for marca in marcas_chile[:5]:
        print(f"  ID: {marca.id} - Nombre: {marca.nombre}")

        # Verificar modelos para esta marca
        modelos = Modelo.objects.filter(marca=marca, pais="CL")
        print(f"    └─ Modelos: {modelos.count()}")
        if modelos.exists():
            for modelo in modelos[:3]:
                print(f"       • {modelo.id}: {modelo.nombre}")
        print()

    # Probar el endpoint interno
    print("\n🧪 PROBANDO LÓGICA DEL ENDPOINT...")
    primera_marca = marcas_chile.first()
    print(f"Probando con marca ID: {primera_marca.id} ({primera_marca.nombre})")

    modelos_api = Modelo.objects.filter(marca_id=primera_marca.id, pais="CL")
    print(f"Modelos encontrados: {modelos_api.count()}")

    # Simular respuesta JSON
    response_data = [
        {"id": modelo.id, "nombre": modelo.nombre} for modelo in modelos_api
    ]

    print("Respuesta JSON simulada:")
    import json

    print(json.dumps(response_data, indent=2, ensure_ascii=False))

else:
    print("❌ No hay marcas para Chile en la base de datos")

print("\n=== FIN VERIFICACIÓN ===")
