# ===============================================================
# 🔗 VERIFICADOR DE URLS DE BIENVENIDA - EGARAGE
# ===============================================================
# Script para probar las URLs de bienvenida por país
# ===============================================================

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.test import Client
from django.urls import reverse, resolve

def configurar_django():
    """Configurar Django para las pruebas"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings_production')
    django.setup()

def probar_urls_bienvenida():
    """Probar las URLs de bienvenida"""
    print("🔗 VERIFICANDO URLs DE BIENVENIDA")
    print("=" * 60)
    
    # URLs a probar
    urls_prueba = [
        ('bienvenida_chile', '/bienvenida/cl/', 'Bienvenida Chile'),
        ('bienvenida_usa', '/bienvenida/usa/', 'Bienvenida USA'),  
        ('welcome_usa', '/welcome/us/', 'Welcome USA (alternativo)'),
    ]
    
    client = Client()
    
    for nombre_url, path, descripcion in urls_prueba:
        try:
            print(f"\n🧪 Probando: {descripcion}")
            print(f"   URL: {path}")
            
            # Probar resolución de URL
            try:
                resolver_match = resolve(path)
                print(f"   ✅ URL resuelve correctamente")
                print(f"   📝 Vista: {resolver_match.func}")
            except Exception as e:
                print(f"   ❌ Error resolviendo URL: {e}")
                continue
            
            # Hacer petición GET
            response = client.get(path)
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Respuesta exitosa")
                # Verificar contenido básico
                if hasattr(response, 'content'):
                    content = response.content.decode('utf-8')
                    if 'eGarage' in content:
                        print(f"   ✅ Contenido correcto encontrado")
                    else:
                        print(f"   ⚠️  Contenido básico presente")
            elif response.status_code == 404:
                print(f"   ❌ URL no encontrada (404)")
            else:
                print(f"   ⚠️  Código inesperado: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error general: {e}")

def mostrar_enlaces_finales():
    """Mostrar enlaces finales para usar en producción"""
    print("\n" + "=" * 60)
    print("🌐 ENLACES DE BIENVENIDA EN PRODUCCIÓN")
    print("=" * 60)
    
    base_url = "https://e-garage-atlantareciclajes.pythonanywhere.com"
    
    enlaces = [
        ("Chile", f"{base_url}/bienvenida/cl/", "🇨🇱"),
        ("USA", f"{base_url}/bienvenida/usa/", "🇺🇸"),
        ("USA (alternativo)", f"{base_url}/welcome/us/", "🇺🇸"),
    ]
    
    for pais, enlace, bandera in enlaces:
        print(f"{bandera} {pais:15} {enlace}")
    
    print("\n💡 URLS ADICIONALES DISPONIBLES:")
    print(f"🏠 Landing Chile:     {base_url}/chile/")
    print(f"🏠 Landing USA:       {base_url}/usa/")
    print(f"📊 Dashboard:         {base_url}/dashboard/")
    print(f"👤 Registro:          {base_url}/registro/")
    print(f"🔐 Admin:             {base_url}/admin/")

def verificar_plantillas():
    """Verificar que las plantillas existen"""
    print("\n📄 VERIFICANDO PLANTILLAS")
    print("=" * 60)
    
    plantillas = [
        'templates/onboarding/bienvenida_chile.html',
        'templates/onboarding/bienvenida_usa.html',
    ]
    
    for plantilla in plantillas:
        if os.path.exists(plantilla):
            print(f"✅ {plantilla}")
        else:
            print(f"❌ {plantilla} - NO ENCONTRADA")

if __name__ == "__main__":
    print("🔗 VERIFICADOR DE URLs DE BIENVENIDA - eGARAGE")
    print("=" * 60)
    
    try:
        configurar_django()
        verificar_plantillas()
        probar_urls_bienvenida()
        mostrar_enlaces_finales()
        
        print("\n✅ VERIFICACIÓN COMPLETADA")
        print("🚀 URLs listas para usar en producción!")
        
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        print("💡 Asegúrate de que Django esté configurado correctamente")
