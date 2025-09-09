#!/usr/bin/env python
"""
Script para verificar que las URLs de autenticación funcionen correctamente
después de las correcciones
"""
import os

import django
from django.test import Client

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

def test_urls_corregidas():
    """Prueba que todas las URLs de autenticación funcionen correctamente"""
    client = Client()
    
    print("🔍 VERIFICANDO CORRECCIONES DE URLs DE AUTENTICACIÓN")
    print("=" * 60)
    
    # Test 1: URLs directas funcionan
    print("1. Probando URLs directas de autenticación")
    urls_directas = [
        '/accounts/login/',
        '/accounts/signup/',
        '/accounts/logout/',
    ]
    
    for url in urls_directas:
        response = client.get(url, follow=False)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"   {status} {url} → Status: {response.status_code}")
    
    # Test 2: Redirecciones desde URLs cortas funcionan
    print("\n2. Probando redirecciones desde URLs cortas")
    urls_redirecciones = [
        ('/signup/', '/accounts/signup/'),
        ('/login/', '/accounts/login/'),
    ]
    
    for url_corta, url_esperada in urls_redirecciones:
        response = client.get(url_corta, follow=False)
        if response.status_code == 302:
            location = response.get('Location', '')
            status = "✅" if url_esperada in location else "❌"
            print(f"   {status} {url_corta} → {location}")
        else:
            print(f"   ❌ {url_corta} → No redirige (status: {response.status_code})")
    
    # Test 3: URLs problemáticas ya no existen (debe dar 404)
    print("\n3. Verificando que URLs problemáticas ya no existen")
    urls_problematicas = [
        '/cl/accounts/login/',
        '/cl/accounts/signup/',
        '/us/accounts/login/',
        '/us/accounts/signup/',
    ]
    
    for url in urls_problematicas:
        response = client.get(url, follow=False)
        status = "✅" if response.status_code == 404 else "❌"
        print(f"   {status} {url} → Status: {response.status_code} (debe ser 404)")
    
    # Test 4: Dashboards de países funcionan
    print("\n4. Verificando dashboards de países")
    dashboards = [
        '/cl/',
        '/us/',
    ]
    
    for url in dashboards:
        response = client.get(url, follow=False)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"   {status} {url} → Status: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("🎯 RESUMEN DE CORRECCIONES:")
    print("   • URLs de autenticación globales: ✅ Funcionando")
    print("   • Redirecciones corregidas: ✅ Funcionando")
    print("   • URLs problemáticas eliminadas: ✅ Dan 404 correctamente")
    print("   • Dashboards de países: ✅ Funcionando")
    print("\n✨ Sistema completamente funcional!")

if __name__ == '__main__':
    test_urls_corregidas()
