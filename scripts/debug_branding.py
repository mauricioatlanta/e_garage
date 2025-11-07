#!/usr/bin/env python
"""
Diagnóstico del sistema de branding
"""
import os

import django
from django.conf import settings
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import RequestFactory

from taller.context_processors import (company_branding, company_context,
                                       empresa_contexto)
from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa


def test_context_processors():
    print("=== TEST CONTEXT PROCESSORS ===")
    
    # Crear request factory
    factory = RequestFactory()
    request = factory.get('/')
    
    # Obtener usuarios existentes
    User = get_user_model()
    users = User.objects.all()
    
    print(f"Usuarios encontrados: {users.count()}")
    
    for user in users[:3]:  # Solo los primeros 3
        print(f"\n--- Usuario: {user.username} ---")
        
        # Simular usuario autenticado
        request.user = user
        
        # Test empresa_contexto
        try:
            context1 = empresa_contexto(request)
            print(f"empresa_contexto: {context1}")
        except Exception as e:
            print(f"Error en empresa_contexto: {e}")
        
        # Test company_branding
        try:
            context2 = company_branding(request)
            print(f"company_branding keys: {list(context2.keys())}")
            print(f"company_logo: {context2.get('company_logo')}")
            print(f"company_name: {context2.get('company_name')}")
        except Exception as e:
            print(f"Error en company_branding: {e}")
        
        # Test company_context
        try:
            context3 = company_context(request)
            print(f"company_context: {context3}")
        except Exception as e:
            print(f"Error en company_context: {e}")

def test_media_settings():
    print("\n=== CONFIGURACIÓN MEDIA ===")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    
    # Verificar que las carpetas existen
    import os
    if os.path.exists(settings.MEDIA_ROOT):
        print(f"MEDIA_ROOT existe: SÍ")
        logos_path = os.path.join(settings.MEDIA_ROOT, 'logos')
        if os.path.exists(logos_path):
            print(f"Carpeta logos existe: SÍ")
            logos = os.listdir(logos_path)
            print(f"Archivos en logos: {logos}")
        else:
            print(f"Carpeta logos existe: NO")
    else:
        print(f"MEDIA_ROOT existe: NO")

def test_logo_urls():
    print("\n=== TEST URLs DE LOGOS ===")
    configs = ConfiguracionEmpresa.objects.filter(logo__isnull=False).exclude(logo='')
    
    for config in configs:
        print(f"\nEmpresa: {config.empresa.nombre_taller}")
        print(f"Logo file: {config.logo}")
        print(f"Logo URL: {config.logo.url}")
        
        # Verificar archivo físico
        try:
            file_exists = config.logo.storage.exists(config.logo.name)
            print(f"Archivo existe: {file_exists}")
            if file_exists:
                file_size = config.logo.size
                print(f"Tamaño: {file_size} bytes")
        except Exception as e:
            print(f"Error verificando archivo: {e}")

if __name__ == "__main__":
    test_context_processors()
    test_media_settings()
    test_logo_urls()
