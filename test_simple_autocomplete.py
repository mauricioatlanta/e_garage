#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Crear cliente de prueba
client = Client()

# Intentar autenticarse con taller2
user = User.objects.filter(username='taller2').first()
if user:
    client.force_login(user)
    print('✅ Autenticado como taller2')
    
    # Probar autocompletado de cliente
    response = client.get('/documentos/autocomplete/cliente/')
    print(f'Cliente autocomplete: {response.status_code}')
    print(f'Content-Type: {response.get("Content-Type", "Not set")}')
    print(f'Response: {response.content[:200]}')
    
    # Probar autocompletado de vehículo
    response = client.get('/documentos/autocomplete/vehiculo/?cliente=5')
    print(f'Vehiculo autocomplete: {response.status_code}')
    print(f'Content-Type: {response.get("Content-Type", "Not set")}')
    print(f'Response: {response.content[:200]}')
else:
    print('❌ Usuario taller2 no encontrado')
