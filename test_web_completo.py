#!/usr/bin/env python3
"""
Script para probar la creación de documentos vía web
Simula el comportamiento de un usuario real
"""
import requests
import json
from bs4 import BeautifulSoup
import time

def test_crear_documento_web():
    print("🌐 === TEST CREACIÓN DOCUMENTO VÍA WEB ===")
    
    # URL base del servidor
    base_url = "http://127.0.0.1:8000"
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    try:
        # 1. Acceder a la página de login
        print("1. Accediendo a la página de login...")
        login_url = f"{base_url}/accounts/login/"
        response = session.get(login_url)
        
        if response.status_code != 200:
            print(f"❌ Error accediendo al login: {response.status_code}")
            return
            
        # Obtener token CSRF
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        print(f"   ✅ Token CSRF obtenido: {csrf_token[:10]}...")
        
        # 2. Hacer login
        print("2. Realizando login...")
        login_data = {
            'csrfmiddlewaretoken': csrf_token,
            'login': 'admin',  # Usuario admin
            'password': 'admin123',  # Contraseña admin
        }
        
        response = session.post(login_url, data=login_data)
        
        if "Sign In" in response.text or response.status_code == 200:
            print("   ✅ Login exitoso")
        else:
            print(f"   ❌ Error en login: {response.status_code}")
            print("   Intentando con usuario de prueba...")
            
        # 3. Acceder al formulario de crear documento
        print("3. Accediendo al formulario de crear documento...")
        crear_url = f"{base_url}/documentos/crear/"
        response = session.get(crear_url)
        
        if response.status_code != 200:
            print(f"   ❌ Error accediendo al formulario: {response.status_code}")
            return
            
        print(f"   ✅ Formulario cargado correctamente")
        
        # Obtener nuevo token CSRF del formulario
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        
        # 4. Preparar datos del documento
        print("4. Preparando datos del documento...")
        
        # Datos básicos del documento
        form_data = {
            'csrfmiddlewaretoken': csrf_token,
            'tipo_documento': 'Orden de trabajo',
            'numero_documento': 'TEST-WEB-001',
            'fecha': '2025-07-22',
            'cliente': '1',  # ID del primer cliente
            'vehiculo': '',  # Sin vehículo
            'kilometraje': '',
            'mecanico': '',
            'observaciones': 'Documento de prueba vía web',
        }
        
        # Datos de repuestos y servicios (JSON)
        items_data = [
            {
                "tipo": "repuesto",
                "partnumber": "WEB-001",
                "nombre": "Repuesto de prueba web",
                "cantidad": 1,
                "precio": 20000
            },
            {
                "tipo": "servicio", 
                "nombre": "Servicio de prueba web",
                "precio": 30000
            }
        ]
        
        form_data['json_items'] = json.dumps(items_data)
        
        print(f"   ✅ Datos preparados:")
        print(f"      - Tipo: {form_data['tipo_documento']}")
        print(f"      - Número: {form_data['numero_documento']}")
        print(f"      - JSON items: {form_data['json_items']}")
        
        # 5. Enviar el formulario
        print("5. Enviando formulario...")
        response = session.post(crear_url, data=form_data)
        
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 302:
            print(f"   ✅ Redirección exitosa a: {response.headers.get('Location', 'URL desconocida')}")
            return True
        elif response.status_code == 200:
            # Verificar si hay errores en el formulario
            if "error" in response.text.lower():
                print("   ❌ Hay errores en el formulario")
                return False
            else:
                print("   ✅ Documento creado exitosamente")
                return True
        else:
            print(f"   ❌ Error inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

def verificar_documento_creado():
    """Verificar si el documento se creó correctamente en la BD"""
    print("\n🔍 === VERIFICACIÓN EN BASE DE DATOS ===")
    
    import os
    import sys
    import django
    
    # Configurar Django
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
    django.setup()
    
    from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
    
    try:
        # Buscar el documento recién creado
        documento = Documento.objects.filter(numero_documento='TEST-WEB-001').first()
        
        if not documento:
            print("❌ Documento TEST-WEB-001 no encontrado en BD")
            return False
            
        print(f"✅ Documento encontrado: {documento.numero_documento}")
        print(f"   Cliente: {documento.cliente}")
        print(f"   Empresa: {documento.empresa.nombre_taller}")
        
        # Verificar repuestos y servicios
        repuestos = RepuestoDocumento.objects.filter(documento=documento)
        servicios = ServicioDocumento.objects.filter(documento=documento)
        
        print(f"   Repuestos en BD: {repuestos.count()}")
        for r in repuestos:
            print(f"     - {r.codigo} | {r.nombre} | ${r.precio} x {r.cantidad}")
            
        print(f"   Servicios en BD: {servicios.count()}")
        for s in servicios:
            print(f"     - {s.nombre} | ${s.precio}")
            
        if repuestos.count() > 0 and servicios.count() > 0:
            print("✅ ¡ÉXITO! El documento tiene repuestos y servicios")
            return True
        else:
            print("❌ PROBLEMA: El documento está vacío")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")
        return False

def main():
    print("🧪 === PRUEBA COMPLETA DEL SISTEMA ===")
    print("Objetivo: Verificar que la creación de documentos funciona correctamente")
    print("=" * 70)
    
    # Esperar un momento para que el servidor esté completamente listo
    print("Esperando que el servidor esté listo...")
    time.sleep(3)
    
    # Probar la creación vía web
    exito_web = test_crear_documento_web()
    
    # Verificar en la base de datos
    if exito_web:
        time.sleep(2)  # Esperar un momento para que se guarde en BD
        exito_bd = verificar_documento_creado()
    else:
        exito_bd = False
    
    # Conclusión
    print("\n" + "=" * 70)
    print("🏁 === RESULTADOS FINALES ===")
    
    if exito_web and exito_bd:
        print("🎉 ¡ÉXITO TOTAL!")
        print("   ✅ El formulario web funciona correctamente")
        print("   ✅ Los repuestos y servicios se guardan en BD")
        print("   ✅ El problema está SOLUCIONADO")
    elif exito_web and not exito_bd:
        print("⚠️ ÉXITO PARCIAL")
        print("   ✅ El formulario web funciona")
        print("   ❌ Los datos no se guardan correctamente")
        print("   🔧 Revisar el procesamiento de json_items")
    else:
        print("❌ PROBLEMA DETECTADO")
        print("   ❌ El formulario web no funciona")
        print("   🔧 Revisar autenticación, formulario o servidor")

if __name__ == "__main__":
    main()
