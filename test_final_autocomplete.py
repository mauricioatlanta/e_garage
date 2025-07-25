#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import json

# Crear cliente de prueba
client = Client()

# Autenticarse con taller2
user = User.objects.filter(username='taller2').first()
if user:
    client.force_login(user)
    print('✅ Autenticado como taller2')
    
    # Probar vehículos para cliente específico (ID 5 = Ricardo Lunari)
    response = client.get('/documentos/autocomplete/vehiculo/?cliente=5')
    print(f'Vehiculos para cliente 5: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Vehículos encontrados: {len(data.get("results", []))}')
        for vehiculo in data.get('results', []):
            print(f'  - {vehiculo}')
    else:
        print(f'Error: {response.content}')
        
    # También probar el cliente autocomplete
    response = client.get('/documentos/autocomplete/cliente/?q=Ricardo')
    print(f'\nClientes con "Ricardo": {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Clientes encontrados: {len(data.get("results", []))}')
        for cliente in data.get('results', []):
            print(f'  - {cliente}')
else:
    print('❌ Usuario taller2 no encontrado')
