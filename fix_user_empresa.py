#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente

# Verificar usuario admin
try:
    user = User.objects.get(username='admin')
    print(f'Usuario: {user.username}')
    print(f'Empresa del usuario: {getattr(user, "empresa", "None")}')
except Exception as e:
    print(f'Error usuario: {e}')

# Verificar cliente 1
try:
    cliente = Cliente.objects.get(id=1)
    print(f'Cliente 1 empresa: {cliente.empresa}')
    print(f'Cliente 1 empresa ID: {cliente.empresa.id}')
    print(f'Cliente 1 país: {cliente.empresa.pais}')
except Exception as e:
    print(f'Error cliente: {e}')

# Listar todas las empresas
print('\nTodas las empresas:')
for empresa in Empresa.objects.all():
    print(f'  ID {empresa.id}: {empresa} - País: {empresa.pais}')

# Asignar usuario admin a empresa USA del cliente 1
try:
    empresa_usa = Empresa.objects.get(id=1)  # USA Test Garage
    user.empresa = empresa_usa
    user.save()
    print(f'\nUsuario admin asignado a empresa USA: {empresa_usa}')
except Exception as e:
    print(f'Error asignando empresa: {e}')
