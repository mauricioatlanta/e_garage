#!/usr/bin/env python3
"""
Test simple de acceso web
"""
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

print("🔧 === TEST DE ACCESO WEB SIMPLE ===")

session = requests.Session()
BASE_URL = "http://127.0.0.1:8000"

# 1. Login directo
print("🔑 Haciendo login como admin...")
login_data = {
    'login': 'admin',
    'password': 'admin123'
}

# Primero obtener la página de login para el CSRF
login_page = session.get(f"{BASE_URL}/accounts/login/")
import re
csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', login_page.text)
if csrf_match:
    login_data['csrfmiddlewaretoken'] = csrf_match.group(1)

# Hacer login
login_response = session.post(f"{BASE_URL}/accounts/login/", data=login_data)
print(f"Login response: {login_response.status_code}")

# 2. Probar crear documento
print("\n📄 Probando crear documento...")
crear_response = session.get(f"{BASE_URL}/documentos/nuevo/")
print(f"Crear documento: {crear_response.status_code}")

if crear_response.status_code == 200:
    print("✅ Crear documento funciona")
    
    # 3. Probar editar un documento existente
    print("\n✏️ Probando editar documento...")
    
    # Primero, listar documentos para encontrar uno existente
    list_response = session.get(f"{BASE_URL}/documentos/")
    print(f"Listar documentos: {list_response.status_code}")
    
    if list_response.status_code == 200:
        # Buscar un documento en la lista
        import re
        doc_links = re.findall(r'/documentos/editar/(\d+)/', list_response.text)
        if doc_links:
            doc_id = doc_links[0]
            print(f"🎯 Probando editar documento ID: {doc_id}")
            
            edit_response = session.get(f"{BASE_URL}/documentos/editar/{doc_id}/")
            print(f"Editar documento: {edit_response.status_code}")
            
            if edit_response.status_code == 200:
                print("✅ Editar documento funciona correctamente")
                
                # Buscar si hay repuestos y servicios en el formulario
                if 'id="repuestosTable"' in edit_response.text:
                    print("✅ Tabla de repuestos encontrada")
                if 'id="serviciosTable"' in edit_response.text:
                    print("✅ Tabla de servicios encontrada")
                if 'formulario_documento.js' in edit_response.text:
                    print("✅ JavaScript del formulario incluido")
            else:
                print(f"❌ Error al editar documento: {edit_response.status_code}")
        else:
            print("⚠️ No se encontraron documentos para editar")
            
    else:
        print(f"❌ Error al listar documentos: {list_response.status_code}")
else:
    print(f"❌ Error al crear documento: {crear_response.status_code}")

print("\n🏁 === FIN TEST SIMPLE ===")
