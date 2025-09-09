#!/usr/bin/env python
"""
Script para verificar rápidamente los datos del catálogo de vehículos
"""
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.db.models import Count

from taller.models.catalogo import CatalogoModeloAuto

print("🚗 VERIFICACIÓN RÁPIDA DEL CATÁLOGO DE VEHÍCULOS")
print("=" * 50)

try:
    # Total de registros
    total = CatalogoModeloAuto.objects.count()
    print(f"📊 Total de modelos: {total:,}")
    
    # Total de marcas únicas
    marcas_count = CatalogoModeloAuto.objects.values('marca').distinct().count()
    print(f"🏷️ Total de marcas: {marcas_count:,}")
    
    print("\n🏆 Top 5 marcas con más modelos:")
    marcas = CatalogoModeloAuto.objects.values('marca').annotate(
        total=Count('modelo')
    ).order_by('-total')[:5]
    
    for i, marca in enumerate(marcas, 1):
        print(f"  {i}. {marca['marca']}: {marca['total']} modelos")
    
    print("\n🚗 Ejemplos de modelos Ford:")
    ford_models = CatalogoModeloAuto.objects.filter(marca='Ford')[:3]
    for model in ford_models:
        print(f"  - {model.modelo}")
    
    print("\n✅ Catálogo verificado correctamente")
    print("🌐 URLs disponibles:")
    print("  - Demo: http://127.0.0.1:8000/demo/catalogo-vehiculos/")
    print("  - Admin: http://127.0.0.1:8000/admin/taller/catalogomodeloauto/")
    print("  - API Stats: http://127.0.0.1:8000/api/catalogo/stats/")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
