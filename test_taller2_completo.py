#!/usr/bin/env python3
"""
Test específico para creación de documentos con taller2
"""
import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models.perfilusuario import PerfilUsuario
from taller.models.empresa import Empresa
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio

print('🧪 === TEST CREACIÓN DOCUMENTOS TALLER2 ===')
print()

# Primero verificar que taller2 puede crear documentos programáticamente
print('1️⃣ Test programático...')
try:
    user_taller2 = User.objects.get(username='taller2')
    perfil_taller2 = PerfilUsuario.objects.get(user=user_taller2)
    
    # Crear documento de prueba
    from datetime import date
    doc_test = Documento.objects.create(
        empresa=perfil_taller2.empresa,
        numero=999,
        fecha=date.today(),
        trabajo_solicitado="Test programático"
    )
    print(f'✅ Documento creado: {doc_test.pk}')
    
    # Agregar repuesto
    repuesto_test = LineaRepuesto.objects.create(
        documento=doc_test,
        codigo="TEST001",
        nombre="Repuesto Test",
        cantidad=1,
        precio_unitario=10000
    )
    print(f'✅ Repuesto creado: {repuesto_test.nombre}')
    
    # Agregar servicio
    servicio_test = LineaServicio.objects.create(
        empresa=perfil_taller2.empresa,
        documento=doc_test,
        nombre="Servicio Test",
        precio_unitario=15000
    )
    print(f'✅ Servicio creado: {servicio_test.nombre}')
    
    print(f'✅ Test programático exitoso - Doc ID: {doc_test.pk}')
    
except Exception as e:
    print(f'❌ Error en test programático: {e}')

print()
print('2️⃣ Test web con taller2...')

# Configurar sesión para test web
session = requests.Session()
BASE_URL = "http://127.0.0.1:8000"

try:
    # Verificar servidor
    response = session.get(f"{BASE_URL}/", timeout=5)
    print(f'   Servidor: {response.status_code}')
    
    # Login con taller2
    login_page = session.get(f"{BASE_URL}/accounts/login/", timeout=5)
    import re
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', login_page.text)
    
    if csrf_match:
        csrf_token = csrf_match.group(1)
        login_data = {
            'csrfmiddlewaretoken': csrf_token,
            'login': 'taller2',
            'password': 'taller2123'
        }
        
        login_response = session.post(
            f"{BASE_URL}/accounts/login/", 
            data=login_data,
            headers={'Referer': f"{BASE_URL}/accounts/login/"},
            timeout=5,
            allow_redirects=False
        )
        
        print(f'   Login taller2: {login_response.status_code}')
        
        if login_response.status_code in [200, 302]:
            # Acceder a crear documento
            crear_doc = session.get(f"{BASE_URL}/documentos/nuevo/", timeout=5)
            print(f'   Página crear: {crear_doc.status_code}')
            
            if crear_doc.status_code == 200:
                # Extraer CSRF para el formulario
                csrf_form = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', crear_doc.text)
                if csrf_form:
                    csrf_form_token = csrf_form.group(1)
                    
                    # Preparar datos del documento con items
                    items_data = [
                        {
                            "tipo": "repuesto",
                            "partnumber": "WEB001",
                            "nombre": "Filtro Aceite Web",
                            "cantidad": 1,
                            "precio": 8000
                        },
                        {
                            "tipo": "servicio",
                            "nombre": "Cambio Aceite Web",
                            "precio": 12000
                        }
                    ]
                    
                    form_data = {
                        'csrfmiddlewaretoken': csrf_form_token,
                        'numero': '888',
                        'fecha': '2025-07-22',
                        'trabajo_solicitado': 'Test web taller2',
                        'json_items': json.dumps(items_data)
                    }
                    
                    # Enviar formulario
                    submit_response = session.post(
                        f"{BASE_URL}/documentos/nuevo/",
                        data=form_data,
                        headers={'Referer': f"{BASE_URL}/documentos/nuevo/"},
                        timeout=5,
                        allow_redirects=False
                    )
                    
                    print(f'   Envío formulario: {submit_response.status_code}')
                    print(f'   Headers: {dict(submit_response.headers)}')
                    
                    # Verificar si se creó el documento
                    docs_after = Documento.objects.filter(empresa__nombre_taller='Mecánica Express').order_by('-pk')
                    if docs_after.exists():
                        ultimo_doc = docs_after.first()
                        repuestos = LineaRepuesto.objects.filter(documento=ultimo_doc)
                        servicios = LineaServicio.objects.filter(documento=ultimo_doc)
                        print(f'   ✅ Último doc: {ultimo_doc.pk} - R:{repuestos.count()} S:{servicios.count()}')
                    else:
                        print('   ⚠️ No se encontraron documentos')
                        
                else:
                    print('   ❌ No se pudo obtener CSRF del formulario')
            else:
                print('   ❌ Error al acceder a crear documento')
        else:
            print('   ❌ Error en login taller2')
    else:
        print('   ❌ No se pudo obtener CSRF de login')

except requests.exceptions.ConnectionError:
    print('   ❌ Servidor no disponible')
except Exception as e:
    print(f'   ❌ Error en test web: {e}')

print()
print('3️⃣ Verificar estado final...')
docs_taller2 = Documento.objects.filter(empresa__nombre_taller='Mecánica Express').order_by('-pk')[:3]
for doc in docs_taller2:
    repuestos = LineaRepuesto.objects.filter(documento=doc)
    servicios = LineaServicio.objects.filter(documento=doc)
    print(f'   Doc {doc.pk}: {doc.trabajo_solicitado[:20]} - R:{repuestos.count()} S:{servicios.count()}')

print()
print('🏁 === FIN TEST ===')
