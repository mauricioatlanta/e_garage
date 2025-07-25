#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

# Crear cliente de prueba
client = Client()

# Autenticarse con taller2
user = User.objects.filter(username='taller2').first()
if user:
    client.force_login(user)
    print('✅ Autenticado como taller2')
    
    # Verificar que la URL de listado existe y funciona
    try:
        lista_url = reverse('documentos:lista_documentos')
        print(f'🔗 URL listado documentos: {lista_url}')
        
        response = client.get(lista_url)
        print(f'📡 GET listado documentos: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ Listado de documentos funciona correctamente')
            print('✅ La redirección debería funcionar correctamente')
        else:
            print(f'❌ Error en listado: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error resolviendo URL: {e}')
        
    # También verificar la URL de ver documento
    try:
        ver_url = reverse('documentos:ver_documento_nuevo', kwargs={'documento_id': 107})
        print(f'🔗 URL ver documento 107: {ver_url}')
        
        response = client.get(ver_url)
        print(f'📡 GET ver documento 107: {response.status_code}')
        
    except Exception as e:
        print(f'❌ Error URL ver documento: {e}')
        
else:
    print('❌ Usuario taller2 no encontrado')
