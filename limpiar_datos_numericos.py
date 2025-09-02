#!/usr/bin/env python
"""
Script para limpiar marcas y modelos con nombres numéricos problemáticos
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo

def main():
    print("🧹 LIMPIEZA: Marcas y modelos con nombres numéricos\n")
    
    # Encontrar marcas con nombres numéricos
    marcas_numericas = Marca.objects.filter(nombre__regex=r'^[0-9]+$')
    print(f"📊 Marcas numéricas encontradas: {marcas_numericas.count()}")
    
    for marca in marcas_numericas:
        print(f"  🔍 Marca problemática: ID {marca.id}, Nombre: '{marca.nombre}'")
        
        # Buscar vehículos que usen esta marca
        vehiculos = Vehiculo.objects.filter(marca=marca)
        print(f"    📋 Vehículos afectados: {vehiculos.count()}")
        
        if vehiculos.exists():
            print("    ⚠️  Vehículos que usan esta marca:")
            for v in vehiculos:
                print(f"      - {v.patente}: {v.marca} {v.modelo}")
    
    # Encontrar modelos con nombres numéricos
    modelos_numericos = Modelo.objects.filter(nombre__regex=r'^[0-9]+$')
    print(f"\n📊 Modelos numéricos encontrados: {modelos_numericos.count()}")
    
    for modelo in modelos_numericos:
        print(f"  🔍 Modelo problemático: ID {modelo.id}, Nombre: '{modelo.nombre}', Marca: {modelo.marca}")
        
        # Buscar vehículos que usen este modelo
        vehiculos = Vehiculo.objects.filter(modelo=modelo)
        print(f"    📋 Vehículos afectados: {vehiculos.count()}")
        
        if vehiculos.exists():
            print("    ⚠️  Vehículos que usan este modelo:")
            for v in vehiculos:
                print(f"      - {v.patente}")
    
    # Proponer corrección
    print(f"\n🔧 PROPUESTA DE CORRECCIÓN:")
    print(f"   1. Actualizar vehículo CCWH63 con marca/modelo correctos")
    print(f"   2. Eliminar marca numérica '8' y modelo numérico '38'")
    print(f"   3. Asignar marca y modelo apropiados según lo que debería ser")

if __name__ == '__main__':
    main()
