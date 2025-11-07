#!/usr/bin/env python
"""
Debug script para verificar el problema de DAL forward con vehículos.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.views_autocomplete import VehiculoAutocomplete

def test_dal_vehiculos():
    print("🔍 Debugging DAL Vehiculos Forward...")
    
    # Crear usuario y empresa de prueba
    try:
        user = User.objects.get(username='testuser_usa')
        empresa = user.empresa
        print(f"✅ Usuario encontrado: {user.username}")
        print(f"✅ Empresa: {empresa.nombre_taller}")
    except User.DoesNotExist:
        print("❌ Usuario testuser_usa no encontrado")
        return
    
    # Buscar clientes de la empresa
    clientes = Cliente.objects.filter(empresa=empresa)
    print(f"📋 Clientes en la empresa: {clientes.count()}")
    
    for cliente in clientes[:3]:  # Mostrar solo los primeros 3
        print(f"  - {cliente.nombre} {cliente.apellido} (ID: {cliente.id})")
    
    # Buscar vehículos de la empresa
    vehiculos = Vehiculo.objects.filter(empresa=empresa)
    print(f"🚗 Vehículos en la empresa: {vehiculos.count()}")
    
    for vehiculo in vehiculos[:3]:  # Mostrar solo los primeros 3
        print(f"  - {vehiculo.patente} - Cliente ID: {vehiculo.cliente_id}")
    
    # Test del VehiculoAutocomplete
    factory = RequestFactory()
    
    # Simular request sin cliente (debería mostrar todos los vehículos de la empresa)
    request = factory.get('/autocomplete/vehiculo/')
    request.user = user
    request.path = '/us/en/autocomplete/vehiculo/'
    
    view = VehiculoAutocomplete()
    view.request = request
    view.forwarded = {}
    
    qs_sin_cliente = view.get_queryset()
    print(f"🚗 Vehículos sin filtrar por cliente: {qs_sin_cliente.count()}")
    
    # Simular request con cliente específico
    if clientes.exists():
        cliente_test = clientes.first()
        request_con_cliente = factory.get(f'/autocomplete/vehiculo/?cliente={cliente_test.id}')
        request_con_cliente.user = user
        request_con_cliente.path = '/us/en/autocomplete/vehiculo/'
        
        view_con_cliente = VehiculoAutocomplete()
        view_con_cliente.request = request_con_cliente
        view_con_cliente.forwarded = {'cliente': str(cliente_test.id)}
        
        qs_con_cliente = view_con_cliente.get_queryset()
        print(f"🚗 Vehículos filtrados por cliente {cliente_test.id}: {qs_con_cliente.count()}")
        
        # Verificar vehículos de este cliente específico
        vehiculos_cliente = Vehiculo.objects.filter(empresa=empresa, cliente=cliente_test)
        print(f"🚗 Vehículos reales del cliente {cliente_test.id}: {vehiculos_cliente.count()}")
        
        for v in vehiculos_cliente:
            print(f"    - {v.patente} - {v.marca} {v.modelo}")

if __name__ == '__main__':
    test_dal_vehiculos()
