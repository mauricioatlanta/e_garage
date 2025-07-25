#!/usr/bin/env python
"""
Test para simular la creación de documento con taller2
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')

# Configurar temporalmente SQLite
import django
from django.conf import settings

settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from taller.documentos.views import crear_documento
import json

def test_crear_documento_taller2():
    print("=== TEST CREACIÓN DOCUMENTO TALLER2 ===\n")
    
    # Obtener usuario taller2
    user = User.objects.get(username='taller2')
    print(f"👤 Usuario: {user.username}")
    
    # Crear request simulado
    factory = RequestFactory()
    
    # Datos del formulario que se enviarían desde el frontend
    form_data = {
        'tipo_documento': 'Presupuesto',
        'numero_documento': 'TALLER2-TEST-3',
        'fecha': '2025-07-23',
        'cliente': 5,  # Ricardo Lunari
        'vehiculo': 5,  # qaqa111 - BMW X3
        'kilometraje': 50000,
        'observaciones': 'Test de documento con datos válidos',
        'json_items': json.dumps([
            {
                'tipo': 'repuesto',
                'partnumber': 'TEST-REP-001',
                'nombre': 'Repuesto Test Válido',
                'cantidad': 2,
                'precio': 15000
            },
            {
                'tipo': 'servicio',
                'nombre': 'Servicio Test Válido',
                'precio': 25000
            }
        ])
    }
    
    print(f"📋 Datos del formulario:")
    print(f"   - Tipo: {form_data['tipo_documento']}")
    print(f"   - Cliente ID: {form_data['cliente']}")
    print(f"   - Vehículo ID: {form_data['vehiculo']}")
    print(f"   - JSON Items: {form_data['json_items']}")
    
    # Crear request POST
    request = factory.post('/documentos/crear/', form_data)
    request.user = user
    
    # Agregar sesión al request
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    print(f"\n🚀 Ejecutando vista crear_documento...")
    
    try:
        response = crear_documento(request)
        print(f"✅ Vista ejecutada exitosamente")
        print(f"   Response status: {response.status_code}")
        print(f"   Response location: {getattr(response, 'url', 'N/A')}")
    except Exception as e:
        print(f"❌ Error en vista: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crear_documento_taller2()
