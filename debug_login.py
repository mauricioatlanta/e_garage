#!/usr/bin/env python3
"""
Test específico para debugging de login
"""
import requests
import re

session = requests.Session()
BASE_URL = "http://127.0.0.1:8000"

print('🐛 === DEBUG LOGIN ===')

try:
    # 1. Verificar página principal
    home = session.get(f"{BASE_URL}/", timeout=5)
    print(f'1. Home page: {home.status_code}')
    
    # 2. Ir a login
    login_page = session.get(f"{BASE_URL}/accounts/login/", timeout=5)
    print(f'2. Login page: {login_page.status_code}')
    
    # Obtener CSRF
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', login_page.text)
    if not csrf_match:
        print('❌ No se encontró CSRF token')
        print('Primeros 500 chars de la página:')
        print(login_page.text[:500])
        exit()
    
    csrf_token = csrf_match.group(1)
    print(f'3. CSRF token: {csrf_token[:10]}...')
    
    # 3. Intentar login con admin
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'login': 'admin',
        'password': 'admin123'
    }
    
    print('4. Enviando datos de login...')
    print(f'   Login data: {login_data}')
    
    login_response = session.post(
        f"{BASE_URL}/accounts/login/",
        data=login_data,
        headers={
            'Referer': f"{BASE_URL}/accounts/login/",
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        timeout=5,
        allow_redirects=False
    )
    
    print(f'5. Response status: {login_response.status_code}')
    print(f'6. Response headers: {dict(login_response.headers)}')
    
    if 'Location' in login_response.headers:
        print(f'7. Redirect to: {login_response.headers["Location"]}')
    
    # Verificar si el login fue exitoso
    if login_response.status_code == 302:
        # Seguir el redirect
        dashboard = session.get(f"{BASE_URL}/dashboard/", timeout=5)
        print(f'8. Dashboard access: {dashboard.status_code}')
        
        if 'admin' in dashboard.text or 'Dashboard' in dashboard.text:
            print('✅ Login exitoso!')
        else:
            print('❌ Login falló - no hay contenido de dashboard')
    else:
        print('❌ Login falló - status code incorrecto')
        print(f'Response content (first 300 chars): {login_response.text[:300]}')

except Exception as e:
    print(f'❌ Error: {e}')

print('\n🏁 === FIN DEBUG ===')
