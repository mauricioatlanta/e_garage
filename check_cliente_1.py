#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.clientes import Cliente

# Buscar el cliente 1
try:
    cliente = Cliente.objects.get(id=1)
    print(f'Cliente: {cliente.nombre} {cliente.apellido}')
    print(f'Empresa: {cliente.empresa if cliente.empresa else "Sin empresa"}')
    print(f'País de la empresa: {cliente.empresa.pais if cliente.empresa else "Sin país"}')
    print(f'Estado USA: {cliente.estado_usa}')
    print(f'Ciudad USA: {cliente.ciudad_usa}')
    print(f'ZIP Code: {cliente.zipcode}')
    print(f'Región: {cliente.region}')
    print(f'Ciudad: {cliente.ciudad}')
    
    # Verificar si tiene estado_usa pero no aparece
    if cliente.estado_usa:
        print(f'El cliente SÍ tiene estado_usa: {cliente.estado_usa.nombre}')
    else:
        print('El cliente NO tiene estado_usa')
        
    if cliente.ciudad_usa:
        print(f'El cliente SÍ tiene ciudad_usa: {cliente.ciudad_usa.nombre}')
    else:
        print('El cliente NO tiene ciudad_usa')
        
except Cliente.DoesNotExist:
    print('Cliente con ID 1 no existe')
except Exception as e:
    print(f'Error: {e}')
