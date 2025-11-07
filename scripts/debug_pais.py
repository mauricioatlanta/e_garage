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
    print(f'Empresa: {cliente.empresa}')
    print(f'Empresa ID: {cliente.empresa.id if cliente.empresa else "None"}')
    print(f'País de la empresa: "{cliente.empresa.pais}" (tipo: {type(cliente.empresa.pais)})')
    print(f'País == "US": {cliente.empresa.pais == "US"}')
    print(f'País == "CL": {cliente.empresa.pais == "CL"}')
    print(f'Repr del país: {repr(cliente.empresa.pais)}')
    
    # Imprimir cada caracter del string pais
    pais = cliente.empresa.pais
    print(f'Caracteres del país: {[c for c in pais]}')
    print(f'Longitud del país: {len(pais)}')
    
    # Verificar si hay espacios o caracteres extraños
    print(f'País stripped: "{pais.strip()}"')
    print(f'País == "US" after strip: {pais.strip() == "US"}')
    
except Cliente.DoesNotExist:
    print('Cliente con ID 1 no existe')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
