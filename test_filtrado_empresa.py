#!/usr/bin/env python
"""
Script para probar que el filtrado por empresa funciona correctamente
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo

def test_filtrado_empresa():
    print("🧪 Probando filtrado por empresa...")
    
    # Crear dos usuarios únicos de prueba
    import time
    timestamp = str(int(time.time()))
    user1 = User.objects.create_user(f'taller1_{timestamp}', 'test1@test.com', 'password')
    user2 = User.objects.create_user(f'taller2_{timestamp}', 'test2@test.com', 'password')
    
    empresa1 = Empresa.objects.create(
        usuario=user1,
        nombre_taller="Taller 1",
        empresa="Empresa 1"
    )
    
    empresa2 = Empresa.objects.create(
        usuario=user2,
        nombre_taller="Taller 2", 
        empresa="Empresa 2"
    )
    
    # Crear clientes para cada empresa
    cliente1 = Cliente.objects.create(
        empresa=empresa1,
        nombre="Cliente Taller 1",
        telefono="111111111"
    )
    
    cliente2 = Cliente.objects.create(
        empresa=empresa2,
        nombre="Cliente Taller 2",
        telefono="222222222"
    )
    
    # Crear vehículos para cada empresa
    vehiculo1 = Vehiculo.objects.create(
        empresa=empresa1,
        cliente=cliente1,
        patente="ABC123"
    )
    
    vehiculo2 = Vehiculo.objects.create(
        empresa=empresa2,
        cliente=cliente2,
        patente="XYZ789"
    )
    
    print(f"✅ Creados:")
    print(f"   - Empresa 1: {empresa1} (ID: {empresa1.id})")
    print(f"   - Empresa 2: {empresa2} (ID: {empresa2.id})")
    print(f"   - Cliente 1: {cliente1} (Empresa {cliente1.empresa.id})")
    print(f"   - Cliente 2: {cliente2} (Empresa {cliente2.empresa.id})")
    print(f"   - Vehículo 1: {vehiculo1} (Empresa {vehiculo1.empresa.id})")
    print(f"   - Vehículo 2: {vehiculo2} (Empresa {vehiculo2.empresa.id})")
    
    # Probar filtrado de clientes por empresa
    clientes_empresa1 = Cliente.objects.filter(empresa=empresa1)
    clientes_empresa2 = Cliente.objects.filter(empresa=empresa2)
    
    print(f"\n🔍 Filtrado de clientes:")
    print(f"   - Empresa 1: {[c.nombre for c in clientes_empresa1]}")
    print(f"   - Empresa 2: {[c.nombre for c in clientes_empresa2]}")
    
    # Probar filtrado de vehículos por empresa
    vehiculos_empresa1 = Vehiculo.objects.filter(empresa=empresa1)
    vehiculos_empresa2 = Vehiculo.objects.filter(empresa=empresa2)
    
    print(f"\n🚗 Filtrado de vehículos:")
    print(f"   - Empresa 1: {[v.patente for v in vehiculos_empresa1]}")
    print(f"   - Empresa 2: {[v.patente for v in vehiculos_empresa2]}")
    
    # Verificar aislamiento
    if len(clientes_empresa1) == 1 and len(clientes_empresa2) == 1:
        if clientes_empresa1[0].empresa.id != clientes_empresa2[0].empresa.id:
            print("\n✅ ÉXITO: Los datos están correctamente aislados por empresa")
        else:
            print("\n❌ ERROR: Los datos NO están aislados por empresa")
    
    # Limpiar datos de prueba
    user1.delete()
    user2.delete()
    empresa1.delete()
    empresa2.delete()
    
    print("\n🧹 Datos de prueba eliminados")

if __name__ == "__main__":
    test_filtrado_empresa()
