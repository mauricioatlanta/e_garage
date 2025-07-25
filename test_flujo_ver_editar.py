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
    
    print('\n🧪 Probando flujo completo para documento 41:')
    
    # 1. Acceder a vista VER documento 41
    ver_url = '/documentos/nuevo-ver/41/'
    print(f'📡 1. GET {ver_url}')
    response = client.get(ver_url)
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 200:
        # Verificar si el template tiene formularios
        content = response.content.decode()
        tiene_form = '<form' in content
        tiene_post = 'method="post"' in content.lower()
        print(f'   ¿Tiene formularios? {tiene_form}')
        print(f'   ¿Tiene POST? {tiene_post}')
        
        # Verificar el enlace de editar
        if 'editar_documento_nuevo' in content:
            print('   ✅ Enlace editar apunta a vista NUEVA')
        elif 'editar_documento' in content:
            print('   ⚠️  Enlace editar apunta a vista ANTIGUA')
        else:
            print('   ❌ No se encontró enlace de editar')
    
    # 2. Acceder a vista EDITAR documento 41
    editar_url = '/documentos/nuevo-editar/41/'
    print(f'\\n📡 2. GET {editar_url}')
    response = client.get(editar_url)
    print(f'   Status: {response.status_code}')
    
    # 3. Verificar URLs disponibles para documento 41
    print(f'\\n🔗 URLs disponibles para documento 41:')
    try:
        ver_nueva = reverse('documentos:ver_documento_nuevo', kwargs={'documento_id': 41})
        print(f'   Ver (nueva): {ver_nueva}')
    except:
        print('   ❌ Ver nueva no disponible')
        
    try:
        editar_nueva = reverse('documentos:editar_documento_nuevo', kwargs={'documento_id': 41})
        print(f'   Editar (nueva): {editar_nueva}')
    except:
        print('   ❌ Editar nueva no disponible')
        
    try:
        lista = reverse('documentos:lista_documentos')
        print(f'   Listado: {lista}')
    except:
        print('   ❌ Listado no disponible')
    
    print(f'\\n🎯 Flujo correcto debería ser:')
    print(f'   1. Ver: {ver_url} (solo lectura)')
    print(f'   2. Clic "Editar" → {editar_url} (formulario)')
    print(f'   3. Guardar cambios → {lista} (listado)')
        
else:
    print('❌ Usuario taller2 no encontrado')
