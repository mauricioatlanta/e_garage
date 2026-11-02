#!/usr/bin/env python
"""
Script para verificar marcas disponibles para USA
Ejecutar con: python manage.py shell < verificar_marcas_usa.py
O desde el shell de Django: exec(open('verificar_marcas_usa.py').read())
"""

import os
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.marca import Marca
from django.db import models

print("=" * 60)
print("VERIFICACIÓN DE MARCAS PARA USA")
print("=" * 60)

# 1. Verificar marcas en el modelo Marca con country="US"
print("\n1. MARCAS EN EL MODELO 'Marca' CON country='US':")
print("-" * 60)

marcas_usa = Marca.objects.filter(country="US").order_by("nombre")
total_marcas_usa = marcas_usa.count()

print(f"Total de marcas encontradas: {total_marcas_usa}")

if total_marcas_usa > 0:
    print("\nPrimeras 20 marcas:")
    for i, marca in enumerate(marcas_usa[:20], 1):
        print(f"  {i}. {marca.nombre} (ID: {marca.id})")
    if total_marcas_usa > 20:
        print(f"  ... y {total_marcas_usa - 20} más")
else:
    print("❌ NO HAY MARCAS en el modelo Marca con country='US'")

# 2. Verificar catálogo (CatalogoModeloAuto)
print("\n2. MARCAS EN EL CATÁLOGO (CatalogoModeloAuto):")
print("-" * 60)

try:
    from taller.models.catalogo import CatalogoModeloAuto

    marcas_catalogo = CatalogoModeloAuto.get_marcas_activas()
    marcas_list = list(marcas_catalogo[:500])
    total_marcas_catalogo = len(marcas_list)

    print(f"Total de marcas en catálogo: {total_marcas_catalogo}")

    if total_marcas_catalogo > 0:
        print("\nPrimeras 20 marcas del catálogo:")
        for i, marca in enumerate(marcas_list[:20], 1):
            print(f"  {i}. {marca}")
        if total_marcas_catalogo > 20:
            print(f"  ... y {total_marcas_catalogo - 20} más")
    else:
        print("❌ NO HAY MARCAS en el catálogo")

    # Verificar total de registros en el catálogo
    total_registros = CatalogoModeloAuto.objects.filter(activo=True).count()
    print(f"\nTotal de registros activos en catálogo: {total_registros}")

except ImportError:
    print("❌ El modelo CatalogoModeloAuto no existe")
except Exception as e:
    print(f"❌ Error al acceder al catálogo: {e}")

# 3. Verificar todas las marcas por país
print("\n3. RESUMEN DE MARCAS POR PAÍS:")
print("-" * 60)

for country_code in ["US", "CL", "MX"]:
    count = Marca.objects.filter(country=country_code).count()
    print(f"  {country_code}: {count} marcas")

# 4. Recomendación
print("\n4. RECOMENDACIÓN:")
print("-" * 60)

if total_marcas_usa > 0:
    print("✅ Hay marcas en el modelo Marca - El formulario debería funcionar")
elif "total_marcas_catalogo" in locals() and total_marcas_catalogo > 0:
    print("✅ Hay marcas en el catálogo - El formulario debería funcionar")
    print("⚠️  Pero no hay marcas en el modelo Marca con country='US'")
    print("   Considera crear marcas en el modelo Marca o poblar el catálogo")
else:
    print("❌ NO HAY MARCAS disponibles para USA")
    print("\n   SOLUCIÓN: Necesitas crear marcas para USA")
    print("   Opciones:")
    print("   1. Crear marcas manualmente en el admin o shell de Django")
    print("   2. Poblar el catálogo con datos de USA")
    print("   3. Importar marcas desde una fuente externa")

print("\n" + "=" * 60)
