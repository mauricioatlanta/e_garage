#!/usr/bin/env python3
"""
Test completo para crear documento con taller2 - vía web
"""
import requests
import re
import json

session = requests.Session()
BASE_URL = "http://127.0.0.1:8000"

print('🧪 === TEST CREAR DOCUMENTO TALLER2 (WEB) ===')

try:
    # 1. Login con taller2
    print('1️⃣ Haciendo login con taller2...')
    login_page = session.get(f"{BASE_URL}/accounts/login/", timeout=5)
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', login_page.text)
    if not csrf_match:
        print('❌ No se pudo obtener CSRF token')
        exit()
    csrf_token = csrf_match.group(1)
    
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'login': 'taller2',
        'password': 'taller2123'
    }
    
    login_response = session.post(f"{BASE_URL}/accounts/login/", data=login_data, allow_redirects=True)
    
    if login_response.status_code == 200 and 'dashboard' in login_response.url.lower():
        print('✅ Login taller2 exitoso')
    else:
        print('❌ Login taller2 falló')
        print(f'Status: {login_response.status_code}')
        print(f'URL final: {login_response.url}')
        exit()
    
    # 2. Acceder a crear documento
    print('2️⃣ Accediendo a crear documento...')
    crear_page = session.get(f"{BASE_URL}/documentos/nuevo/", timeout=5)
    
    if crear_page.status_code != 200:
        print(f'❌ Error al acceder a crear documento: {crear_page.status_code}')
        exit()
    
    print('✅ Página de crear documento cargada')
    
    # 3. Obtener CSRF del formulario
    csrf_form_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', crear_page.text)
    if not csrf_form_match:
        print('❌ No se pudo obtener CSRF del formulario')
        exit()
    
    csrf_form_token = csrf_form_match.group(1)
    print(f'✅ CSRF del formulario obtenido: {csrf_form_token[:10]}...')
    
    # 4. Buscar opciones de cliente disponibles
    print('3️⃣ Buscando clientes disponibles...')
    clientes_response = session.get(f"{BASE_URL}/autocomplete/cliente/?q=", timeout=5)
    
    if clientes_response.status_code == 200:
        try:
            clientes_data = clientes_response.json()
            if clientes_data.get("results"):
                cliente_id = clientes_data["results"][0]["id"]
                cliente_nombre = clientes_data["results"][0]["text"]
                print(f'✅ Cliente encontrado: {cliente_nombre} (ID: {cliente_id})')
            else:
                print('⚠️ No hay clientes, usando ID 1 por defecto')
                cliente_id = 1
        except:
            print('⚠️ Error al parsear clientes, usando ID 1 por defecto')
            cliente_id = 1
    else:
        print(f'⚠️ Error al obtener clientes ({clientes_response.status_code}), usando ID 1')
        cliente_id = 1
    
    # 5. Preparar datos del documento
    print('4️⃣ Preparando datos del documento...')
    
    items_data = [
        {
            "tipo": "repuesto",
            "partnumber": "TEST-REP-T2",
            "nombre": "Repuesto Test Taller2",
            "cantidad": 1,
            "precio": 12000
        },
        {
            "tipo": "servicio",
            "nombre": "Servicio Test Taller2", 
            "precio": 20000
        }
    ]
    
    documento_data = {
        'csrfmiddlewaretoken': csrf_form_token,
        'tipo_documento': 'Presupuesto',
        'numero_documento': 'T2-WEB-001',
        'fecha': '2025-07-22',
        'cliente': str(cliente_id),
        'kilometraje': '75000',
        'observaciones': 'Test documento web taller2',
        'json_items': json.dumps(items_data)
    }
    
    print(f'✅ Datos preparados con {len(items_data)} items')
    
    # 6. Enviar formulario
    print('5️⃣ Enviando formulario...')
    
    create_response = session.post(
        f"{BASE_URL}/documentos/nuevo/",
        data=documento_data,
        headers={
            'Referer': f"{BASE_URL}/documentos/nuevo/",
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        timeout=10,
        allow_redirects=False
    )
    
    print(f'Response status: {create_response.status_code}')
    print(f'Response headers: {dict(create_response.headers)}')
    
    if create_response.status_code == 302:
        redirect_url = create_response.headers.get('Location', '')
        print(f'✅ Documento creado - Redirect a: {redirect_url}')
        
        # Seguir el redirect
        if redirect_url:
            final_page = session.get(f"{BASE_URL}{redirect_url}", timeout=5)
            print(f'Página final: {final_page.status_code}')
            
    elif create_response.status_code == 200:
        print('⚠️ Formulario devuelto (posibles errores)')
        # Buscar errores específicos
        response_text = create_response.text.lower()
        if 'error' in response_text:
            print('❌ Errores encontrados en la respuesta')
        if 'required' in response_text:
            print('❌ Campos requeridos faltantes')
        
        print(f'Primeros 300 chars: {create_response.text[:300]}')
        
    else:
        print(f'❌ Error inesperado: {create_response.status_code}')

except Exception as e:
    print(f'❌ Error en el test: {e}')
    import traceback
    traceback.print_exc()

print('\n🏁 === FIN TEST WEB ===')
