#!/usr/bin/env python3
"""
Script para probar URLs y verificar que funcionan
"""
import os
import sys
import django
import requests

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.mecanico import Mecanico
from taller.models.perfilusuario import PerfilUsuario

def test_urls():
    """
    Probar URLs de configuración
    """
    print("🔧 Probando URLs de configuración...")
    
    # Crear cliente de prueba
    client = Client()
    
    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Usuario de prueba creado: {user.username}")
    
    # Crear empresa
    empresa, created = Empresa.objects.get_or_create(
        usuario=user,
        defaults={
            'nombre_taller': 'Taller de Prueba',
            'telefono': '123456789',
            'email': 'taller@test.com'
        }
    )
    
    if created:
        print(f"✅ Empresa creada: {empresa.nombre_taller}")
    
    # Crear perfil
    perfil, created = PerfilUsuario.objects.get_or_create(
        user=user,
        defaults={
            'empresa': empresa
        }
    )
    
    if created:
        print(f"✅ Perfil creado")
    
    # Crear algunos mecánicos
    mecanicos_datos = [
        {'nombre': 'Juan Pérez', 'activo': True},
        {'nombre': 'María García', 'activo': True},
        {'nombre': 'Carlos López', 'activo': False},
    ]
    
    for mec_data in mecanicos_datos:
        mecanico, created = Mecanico.objects.get_or_create(
            empresa=empresa,
            nombre=mec_data['nombre'],
            defaults={'activo': mec_data['activo']}
        )
        
        if created:
            status = "✅ ACTIVO" if mecanico.activo else "❌ INACTIVO"
            print(f"{status} Mecánico creado: {mecanico.nombre}")
    
    # Autenticar usuario
    client.force_login(user)
    
    # Probar URLs
    urls_to_test = [
        ('/configuracion/', 'Configuración Principal'),
        ('/configuracion/mecanicos/', 'Gestión de Mecánicos'),
    ]
    
    for url, description in urls_to_test:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ {description}: {url} - OK")
            else:
                print(f"❌ {description}: {url} - Error {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: {url} - Excepción: {e}")
    
    print("\n📝 URLs para probar manualmente:")
    print("http://127.0.0.1:8000/configuracion/")
    print("http://127.0.0.1:8000/configuracion/mecanicos/")
    print(f"\nUsuario de prueba: {user.username} / testpass123")

if __name__ == '__main__':
    test_urls()
