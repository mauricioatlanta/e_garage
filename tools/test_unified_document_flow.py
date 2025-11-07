#!/usr/bin/env python3
"""
Script de verificación del flujo unificado de creación de documentos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.urls import reverse
from taller.documentos.api import (
    clientes_search, vehiculos_por_cliente, repuestos_search, 
    servicios_search, obtener_numero_documento
)

def test_api_endpoints():
    """Probar todos los endpoints de API"""
    print("🧪 PROBANDO ENDPOINTS DE API")
    print("=" * 50)
    
    factory = RequestFactory()
    
    # Obtener usuario de prueba
    user = User.objects.first()
    if not user:
        print("❌ No hay usuarios en la base de datos")
        return
    
    print(f"👤 Usando usuario: {user.username}")
    
    # 1. API de clientes
    print("\n1️⃣ Probando API de clientes...")
    try:
        request = factory.get('/us/documentos/api/clientes/search/?q=da')
        request.user = user
        response = clientes_search(request)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Clientes encontrados: {len(data.get('clientes', []))}")
            for cliente in data.get('clientes', [])[:3]:
                print(f"   - {cliente.get('nombre', 'N/A')} ({cliente.get('tax_id', 'N/A')})")
        else:
            print(f"   Error: {response.content.decode()}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 2. API de repuestos
    print("\n2️⃣ Probando API de repuestos...")
    try:
        request = factory.get('/us/documentos/api/repuestos/search/?q=mo')
        request.user = user
        response = repuestos_search(request)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Repuestos encontrados: {len(data.get('repuestos', []))}")
            for repuesto in data.get('repuestos', [])[:3]:
                print(f"   - {repuesto.get('nombre', 'N/A')} (${repuesto.get('precio', 0)})")
        else:
            print(f"   Error: {response.content.decode()}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 3. API de servicios
    print("\n3️⃣ Probando API de servicios...")
    try:
        request = factory.get('/us/documentos/api/servicios/search/?q=oil')
        request.user = user
        response = servicios_search(request)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Servicios encontrados: {len(data.get('servicios', []))}")
            for servicio in data.get('servicios', [])[:3]:
                print(f"   - {servicio.get('nombre', 'N/A')} (${servicio.get('precio', 0)})")
        else:
            print(f"   Error: {response.content.decode()}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 4. API de número de documento
    print("\n4️⃣ Probando API de número de documento...")
    for tipo in ['FAC', 'PRES', 'OT']:
        try:
            request = factory.get(f'/us/documentos/api/obtener-numero-documento/?tipo={tipo}')
            request.user = user
            response = obtener_numero_documento(request)
            print(f"   {tipo}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Número generado: {data.get('numero', 'N/A')}")
            else:
                print(f"   Error: {response.content.decode()}")
        except Exception as e:
            print(f"   ❌ Error para {tipo}: {str(e)}")

def test_urls():
    """Probar que las URLs estén configuradas correctamente"""
    print("\n🔗 VERIFICANDO CONFIGURACIÓN DE URLs")
    print("=" * 50)
    
    client = Client()
    user = User.objects.first()
    
    if not user:
        print("❌ No hay usuarios para probar autenticación")
        return
    
    client.force_login(user)
    
    # URLs a probar
    urls_to_test = [
        '/us/documentos/form/',
        '/us/documentos/api/clientes/search/?q=test',
        '/us/documentos/api/repuestos/search/?q=test',
        '/us/documentos/api/servicios/search/?q=test',
        '/us/documentos/api/obtener-numero-documento/?tipo=FAC',
    ]
    
    for url in urls_to_test:
        try:
            response = client.get(url)
            status_emoji = "✅" if response.status_code == 200 else "⚠️"
            print(f"{status_emoji} {url} -> {response.status_code}")
        except Exception as e:
            print(f"❌ {url} -> Error: {str(e)}")

def check_files():
    """Verificar que los archivos necesarios existan"""
    print("\n📁 VERIFICANDO ARCHIVOS")
    print("=" * 50)
    
    files_to_check = [
        'taller/documentos/api.py',
        'static/js/documento_form_advanced.js',
        'templates/taller/documentos/formulario_documento.html',
        'taller/documentos/urls.py',
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NO EXISTE")

def main():
    print("🚀 VERIFICACIÓN DEL FLUJO UNIFICADO DE DOCUMENTOS")
    print("=" * 60)
    
    check_files()
    test_api_endpoints()
    test_urls()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMEN DE VERIFICACIÓN COMPLETADO")
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Acceder a /us/documentos/form/")
    print("2. Verificar que solo se carga documento_form_advanced.js")
    print("3. Probar cambio de tipo de documento (debe cambiar color)")
    print("4. Probar búsqueda de clientes, repuestos y servicios")
    print("5. Verificar generación automática de números")

if __name__ == "__main__":
    main()

