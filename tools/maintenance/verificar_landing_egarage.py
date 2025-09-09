#!/usr/bin/env python
"""
Script para verificar URLs específicas de landing de eGarage
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import Client
from django.conf import settings

def verificar_landing_egarage():
    """Verificar URLs de landing de eGarage"""
    print("🔗 VERIFICANDO LANDING PAGES DE eGARAGE")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # URLs de landing a probar
    urls_landing = [
        ('egarage/', 'Landing Principal eGarage'),
        ('egarage-pro/', 'Landing Pro eGarage'),
        ('landing/', 'Landing Premium'),
        ('', 'Página de inicio'),
    ]
    
    client = Client()
    
    print(f"\n🌐 SERVIDOR LOCAL: {base_url}")
    print("-" * 60)
    
    for url_path, descripcion in urls_landing:
        full_url = f"{base_url}/{url_path}"
        try:
            response = client.get(f"/{url_path}")
            status_code = response.status_code
            
            if status_code == 200:
                status = "✅ DISPONIBLE"
            elif status_code == 302:
                status = "🔄 REDIRECT"
            elif status_code == 404:
                status = "❌ NO CONFIGURADO"
            else:
                status = f"⚠️ {status_code}"
                
            print(f"{status:<15} {full_url:<50} {descripcion}")
            
        except Exception as e:
            print(f"❌ ERROR       {full_url:<50} {descripcion} - {str(e)}")
    
    print("\n" + "=" * 60)
    print("🇨🇱 PÁGINA PRINCIPAL PARA CHILE:")
    print("La landing page principal con planes y características está en:")
    print(f"✨ {base_url}/egarage/ (si está configurado)")
    print(f"✨ {base_url}/egarage-pro/ (alternativa)")
    
    print("\n📋 CONTENIDO DE LA LANDING:")
    print("• 🚀 Planes de precios en CLP y USD")
    print("• ✨ Características del producto")
    print("• 🎯 Call-to-action para prueba gratis")
    print("• 📊 Beneficios específicos para talleres")
    print("• 🔧 Funcionalidades detalladas")
    
    print("\n💡 INSTRUCCIONES:")
    print("1. Iniciar servidor: python manage.py runserver")
    print("2. Si las URLs no están configuradas, revisar gestion_taller/urls.py")
    print("3. La landing completa está en templates/landing_egarage.html")

if __name__ == "__main__":
    verificar_landing_egarage()
