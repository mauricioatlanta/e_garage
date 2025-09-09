#!/usr/bin/env python
"""
Script para verificar URLs locales de eGarage
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.conf import settings

def verificar_urls_locales():
    """Verificar URLs locales disponibles"""
    print("🔗 VERIFICANDO URLs LOCALES DE eGARAGE")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # URLs a probar
    urls_prueba = [
        ('', 'Página principal'),
        ('cl/', 'Dashboard Chile'),
        ('us/', 'Dashboard USA'),
        ('chile/', 'Landing Chile'),
        ('usa/', 'Landing USA'),
        ('bienvenida/cl/', 'Bienvenida Chile'),
        ('bienvenida/usa/', 'Bienvenida USA'),
        ('welcome/us/', 'Welcome USA'),
        ('dashboard/', 'Dashboard'),
        ('admin/', 'Admin'),
        ('accounts/login/', 'Login'),
        ('registro/', 'Registro'),
    ]
    
    client = Client()
    
    print(f"\n🌐 SERVIDOR LOCAL: {base_url}")
    print("-" * 60)
    
    for url_path, descripcion in urls_prueba:
        full_url = f"{base_url}/{url_path}"
        try:
            response = client.get(f"/{url_path}")
            status_code = response.status_code
            
            if status_code == 200:
                status = "✅ OK"
            elif status_code == 302:
                status = "🔄 REDIRECT"
            elif status_code == 404:
                status = "❌ 404"
            else:
                status = f"⚠️ {status_code}"
                
            print(f"{status:<12} {full_url:<50} {descripcion}")
            
        except Exception as e:
            print(f"❌ ERROR    {full_url:<50} {descripcion} - {str(e)}")
    
    print("\n" + "=" * 60)
    print("💡 INSTRUCCIONES PARA USAR:")
    print("1. Iniciar servidor: python manage.py runserver")
    print("2. Abrir navegador en la URL que necesites")
    print("3. Si una URL muestra ❌ 404, significa que no está configurada localmente")
    
    # URLs específicas para Chile
    print(f"\n🇨🇱 ENLACES ESPECÍFICOS PARA CHILE:")
    print(f"   • Dashboard: {base_url}/cl/")
    print(f"   • Landing:   {base_url}/chile/")
    print(f"   • Bienvenida: {base_url}/bienvenida/cl/ (si está configurado)")
    
    print(f"\n🇺🇸 ENLACES ESPECÍFICOS PARA USA:")
    print(f"   • Dashboard: {base_url}/us/")
    print(f"   • Landing:   {base_url}/usa/")
    print(f"   • Bienvenida: {base_url}/bienvenida/usa/ (si está configurado)")

if __name__ == "__main__":
    verificar_urls_locales()
