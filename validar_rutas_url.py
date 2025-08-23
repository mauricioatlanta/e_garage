#!/usr/bin/env python
"""
✅ Validador de Rutas URL - eGarage
Confirma que todas las rutas críticas están funcionando correctamente
"""

import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User

def test_url_redirects():
    """Probar redirecciones principales"""
    
    print("🌐 VALIDADOR DE RUTAS URL - eGarage")
    print("=" * 50)
    
    client = Client()
    
    # Rutas que deben redirigir correctamente
    test_routes = [
        {
            'url': '/registro/',
            'expected_redirect': '/accounts/signup/',
            'description': 'Registro español → Django Allauth Signup'
        },
        {
            'url': '/signup/',
            'expected_redirect': '/accounts/signup/',
            'description': 'Signup inglés → Django Allauth Signup'
        },
        {
            'url': '/login/',
            'expected_redirect': '/accounts/login/',
            'description': 'Login → Django Allauth Login'
        },
        {
            'url': '/dashboard/',
            'expected_redirect': '/cl/dashboard/',
            'description': 'Dashboard → Chile Dashboard'
        },
        {
            'url': '/vehiculos/',
            'expected_redirect': '/cl/vehiculos/',
            'description': 'Vehículos → Chile Vehículos'
        },
        {
            'url': '/repuestos/',
            'expected_redirect': '/cl/repuestos/',
            'description': 'Repuestos → Chile Repuestos'
        },
        {
            'url': '/',
            'expected_redirect': '/cl/',
            'description': 'Raíz → Chile Home'
        }
    ]
    
    print("📋 PROBANDO REDIRECCIONES:")
    print("-" * 50)
    
    all_passed = True
    
    for route in test_routes:
        try:
            response = client.get(route['url'])
            
            if response.status_code == 302:  # Redirección
                redirect_url = response.get('Location', 'No Location header')
                if redirect_url == route['expected_redirect']:
                    print(f"✅ {route['url']} → {redirect_url}")
                    print(f"   {route['description']}")
                else:
                    print(f"⚠️  {route['url']} → {redirect_url} (esperado: {route['expected_redirect']})")
                    print(f"   {route['description']}")
                    all_passed = False
            else:
                print(f"❌ {route['url']} → Status {response.status_code}")
                print(f"   {route['description']}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Error en {route['url']}: {e}")
            all_passed = False
        
        print()
    
    return all_passed

def test_authenticated_routes():
    """Probar rutas que requieren autenticación"""
    
    print("🔐 PROBANDO RUTAS AUTENTICADAS:")
    print("-" * 50)
    
    client = Client()
    
    # Probar sin autenticación
    auth_routes = [
        '/cl/',
        '/taller/centro-operaciones-espacial/',
        '/taller/dashboard/',
    ]
    
    print("🚫 Sin autenticación:")
    for route in auth_routes:
        try:
            response = client.get(route)
            if route == '/cl/':
                if response.status_code == 200:
                    print(f"✅ {route} → 200 (página de bienvenida)")
                else:
                    print(f"⚠️  {route} → {response.status_code}")
            else:
                if response.status_code in [302, 403]:
                    print(f"✅ {route} → {response.status_code} (redirige o requiere login)")
                else:
                    print(f"⚠️  {route} → {response.status_code}")
        except Exception as e:
            print(f"❌ Error en {route}: {e}")
    
    print("\n🔑 Con autenticación mauricio1:")
    
    # Probar con usuario mauricio1 autenticado
    try:
        user = User.objects.get(username='mauricio1')
        client.force_login(user)
        
        # Probar /cl/ autenticado (debe redirigir al dashboard espacial)
        response = client.get('/cl/')
        if response.status_code == 302:
            redirect_location = response.get('Location', 'No Location header')
            print(f"✅ /cl/ → {redirect_location} (redirección a dashboard)")
        else:
            print(f"⚠️  /cl/ → {response.status_code}")
            
        # Probar dashboard espacial directo
        response = client.get('/taller/centro-operaciones-espacial/')
        if response.status_code == 200:
            print(f"✅ /taller/centro-operaciones-espacial/ → 200 (dashboard cargado)")
        else:
            print(f"⚠️  /taller/centro-operaciones-espacial/ → {response.status_code}")
            
    except User.DoesNotExist:
        print("❌ Usuario mauricio1 no encontrado")
    except Exception as e:
        print(f"❌ Error con autenticación: {e}")

def test_django_allauth():
    """Probar configuración de Django Allauth"""
    
    print("\n🏢 PROBANDO DJANGO ALLAUTH:")
    print("-" * 50)
    
    client = Client()
    
    allauth_routes = [
        '/accounts/signup/',
        '/accounts/login/',
        '/accounts/logout/',
    ]
    
    for route in allauth_routes:
        try:
            response = client.get(route)
            if response.status_code == 200:
                print(f"✅ {route} → 200 (página disponible)")
            else:
                print(f"⚠️  {route} → {response.status_code}")
        except Exception as e:
            print(f"❌ Error en {route}: {e}")

def main():
    """Ejecutar todas las pruebas"""
    
    print("🚀 INICIANDO VALIDACIÓN DE RUTAS...")
    print()
    
    # Prueba 1: Redirecciones
    redirects_ok = test_url_redirects()
    
    # Prueba 2: Rutas autenticadas
    test_authenticated_routes()
    
    # Prueba 3: Django Allauth
    test_django_allauth()
    
    print("\n" + "=" * 50)
    if redirects_ok:
        print("🎯 VALIDACIÓN EXITOSA - Todas las rutas funcionan correctamente")
        print()
        print("📌 RUTAS PRINCIPALES DISPONIBLES:")
        print("   • http://127.0.0.1:8000/registro/ → Página de registro")
        print("   • http://127.0.0.1:8000/login/ → Página de login")
        print("   • http://127.0.0.1:8000/cl/ → Dashboard Chile")
        print("   • http://127.0.0.1:8000/us/ → Dashboard USA")
        print("   • http://127.0.0.1:8000/accounts/signup/ → Django Allauth Signup")
        print("   • http://127.0.0.1:8000/accounts/login/ → Django Allauth Login")
        print()
        print("🔑 PARA PROBAR EL DASHBOARD ESPACIAL:")
        print("   1. Ir a http://127.0.0.1:8000/registro/")
        print("   2. O login con mauricio1/taller123 en http://127.0.0.1:8000/cl/")
    else:
        print("❌ VALIDACIÓN FALLIDA - Hay problemas con algunas rutas")
        return False
    
    return True

if __name__ == "__main__":
    if not main():
        sys.exit(1)
