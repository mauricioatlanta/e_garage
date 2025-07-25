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

# Autenticarse con taller2
user = User.objects.filter(username='taller2').first()
if user:
    client.force_login(user)
    print('✅ Autenticado como taller2')
    
    # Obtener el formulario de edición del documento 107
    response = client.get('/documentos/nuevo-editar/107/')
    print(f'📡 GET edición documento 107: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ Formulario de edición cargado correctamente')
        
        # Simular POST con datos mínimos
        csrf_token = response.context['csrf_token']
        
        post_data = {
            'csrfmiddlewaretoken': csrf_token,
            'tipo_documento': 'Factura',
            'numero_documento': 'F-009',
            'fecha': '2025-07-23',
            'cliente': '5',  # Ricardo Lunari
            'kilometraje': '50000',
            'observaciones': 'Test de redirección',
            'incluir_iva': 'on',
            'json_items': '[]'  # Sin items para simplicidad
        }
        
        print('🚀 Simulando guardado...')
        response = client.post('/documentos/nuevo-editar/107/', post_data, follow=True)
        
        print(f'📡 POST resultado: {response.status_code}')
        print(f'🔄 Redirecciones: {len(response.redirect_chain)}')
        
        if response.redirect_chain:
            for i, (url, status) in enumerate(response.redirect_chain):
                print(f'   {i+1}. {url} ({status})')
                
        final_url = response.wsgi_request.path
        print(f'🎯 URL final: {final_url}')
        
        if '/documentos/' == final_url and not 'editar' in final_url and not 'ver' in final_url:
            print('✅ Redirección correcta al listado de documentos')
        else:
            print(f'❌ Redirección incorrecta, esperaba listado pero llegó a: {final_url}')
            
    else:
        print(f'❌ Error cargando formulario: {response.status_code}')
        
else:
    print('❌ Usuario taller2 no encontrado')
