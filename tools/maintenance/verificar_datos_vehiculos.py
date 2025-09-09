#!/usr/bin/env python3

import os
import sys

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo


def verificar_datos_vehiculos():
    print("=== VERIFICANDO DATOS PARA CARGA DE VEHÍCULOS ===")
    
    # Verificar empresas
    empresas = Empresa.objects.all()
    print(f"📊 Empresas encontradas: {empresas.count()}")
    
    for empresa in empresas:
        print(f"\n🏢 Empresa: {empresa.nombre_taller} (País: {empresa.pais})")
        
        # Clientes de esta empresa
        clientes = Cliente.objects.filter(empresa=empresa)
        print(f"👥 Clientes: {clientes.count()}")
        
        for cliente in clientes[:3]:  # Solo mostrar los primeros 3
            print(f"   - {cliente.nombre} (ID: {cliente.id})")
            
            # Vehículos de este cliente
            vehiculos = Vehiculo.objects.filter(cliente=cliente)
            print(f"     🚗 Vehículos: {vehiculos.count()}")
            
            for vehiculo in vehiculos:
                marca = vehiculo.marca.nombre if vehiculo.marca else 'Sin marca'
                modelo = vehiculo.modelo.nombre if vehiculo.modelo else 'Sin modelo'
                print(f"       - {vehiculo.patente} - {marca} {modelo} ({vehiculo.anio})")
    
    print("\n=== RESUMEN ===")
    total_clientes = Cliente.objects.count()
    total_vehiculos = Vehiculo.objects.count()
    print(f"✅ Total clientes: {total_clientes}")
    print(f"✅ Total vehículos: {total_vehiculos}")
    
    if total_clientes == 0:
        print("⚠️  No hay clientes. Crear algunos clientes primero.")
    elif total_vehiculos == 0:
        print("⚠️  No hay vehículos. Crear algunos vehículos primero.")
    else:
        print("✅ Datos disponibles para probar la carga de vehículos")

if __name__ == "__main__":
    verificar_datos_vehiculos()
