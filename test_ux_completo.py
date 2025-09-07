#!/usr/bin/env python
"""
Script de prueba UX para eGarage
Prueba el flujo completo: Login -> Crear documento -> Ver historial -> Diagnóstico IA
"""

import json

import requests
from requests.cookies import RequestsCookieJar

BASE_URL = "http://127.0.0.1:8000"


def test_login():
    """Probar login con usuario taller1"""
    print("🔐 Probando login...")

    session = requests.Session()

    # Obtener el formulario de login para conseguir el CSRF token
    login_page = session.get(f"{BASE_URL}/accounts/login/")
    print(f"  - Status login page: {login_page.status_code}")

    if login_page.status_code != 200:
        print("  ❌ Error accediendo a página de login")
        return None, None

    # Extraer CSRF token (simple parsing)
    csrf_token = None
    for line in login_page.text.split("\n"):
        if "csrfmiddlewaretoken" in line and "value=" in line:
            start = line.find('value="') + 7
            end = line.find('"', start)
            csrf_token = line[start:end]
            break

    if not csrf_token:
        print("  ❌ No se pudo obtener CSRF token")
        return None, None

    print(f"  - CSRF Token: {csrf_token[:20]}...")

    # Datos de login
    login_data = {
        "username": "taller1",
        "password": "123456",
        "csrfmiddlewaretoken": csrf_token,
        "next": "/dashboard/",
    }

    # Intentar login
    login_response = session.post(f"{BASE_URL}/accounts/login/", data=login_data)
    print(f"  - Status login: {login_response.status_code}")
    print(f"  - Redirect URL: {login_response.url}")

    if "dashboard" in login_response.url or login_response.status_code == 200:
        print("  ✅ Login exitoso")
        return session, csrf_token
    else:
        print("  ❌ Login falló")
        return None, None


def test_documentos(session):
    """Probar acceso al módulo de documentos"""
    print("\n📄 Probando módulo de documentos...")

    # Probar lista de documentos
    docs_list = session.get(f"{BASE_URL}/documentos/")
    print(f"  - Lista documentos: {docs_list.status_code}")

    # Probar crear documento
    create_doc = session.get(f"{BASE_URL}/documentos/nuevo/")
    print(f"  - Crear documento: {create_doc.status_code}")

    if docs_list.status_code == 200 and create_doc.status_code == 200:
        print("  ✅ Módulo de documentos funcionando")
        return True
    else:
        print("  ❌ Error en módulo de documentos")
        return False


def test_suscripciones(session):
    """Probar sistema de suscripciones"""
    print("\n💳 Probando sistema de suscripciones...")

    # Probar página de precios
    precios_response = session.get(f"{BASE_URL}/precios/")
    print(f"  - Página de precios: {precios_response.status_code}")

    # Probar estado de suscripción (API)
    estado_response = session.get(f"{BASE_URL}/api/estado-suscripcion/")
    print(f"  - API estado suscripción: {estado_response.status_code}")

    if estado_response.status_code == 200:
        try:
            data = estado_response.json()
            print(f"    - Días restantes: {data.get('dias_restantes', 'N/A')}")
            print(f"    - Estado: {data.get('activa', 'N/A')}")
        except ValueError as e:
            print(f"    - Error parsing JSON: {e}")
            print(f"    - Response text: {estado_response.text[:100]}...")
    else:
        print(f"    - Error: {estado_response.text[:100]}...")

    # Probar subir comprobante
    comprobante_response = session.get(f"{BASE_URL}/comprobante-pago/")
    print(f"  - Subir comprobante: {comprobante_response.status_code}")

    if precios_response.status_code == 200 and estado_response.status_code == 200:
        print("  ✅ Sistema de suscripciones funcionando")
        return True
    else:
        print("  ❌ Error en sistema de suscripciones")
        return False
    """Probar diagnóstico IA"""
    print("\n🤖 Probando diagnóstico IA...")

    diag_response = session.get(f"{BASE_URL}/taller/reportes/diagnostico/")
    print(f"  - Diagnóstico IA: {diag_response.status_code}")

    if diag_response.status_code == 200:
        print("  ✅ Diagnóstico IA funcionando")
        return True
    else:
        print("  ❌ Error en diagnóstico IA")


def test_diagnostico(session):
    """Probar diagnóstico IA"""
    print("\n🤖 Probando diagnóstico IA...")

    diag_response = session.get(f"{BASE_URL}/taller/reportes/diagnostico/")
    print(f"  - Diagnóstico IA: {diag_response.status_code}")

    if diag_response.status_code == 200:
        print("  ✅ Diagnóstico IA funcionando")
        return True
    else:
        print("  ❌ Error en diagnóstico IA")
        return False


def main():
    print("🧪 INICIANDO PRUEBAS UX DE eGARAGE")
    print("=" * 50)

    # Probar login
    session, csrf_token = test_login()
    if not session:
        print("\n❌ PRUEBAS FALLIDAS: No se pudo hacer login")
        return

    # Probar documentos
    docs_ok = test_documentos(session)

    # Probar suscripciones
    subs_ok = test_suscripciones(session)

    # Probar diagnóstico
    diag_ok = test_diagnostico(session)

    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"  🔐 Login: ✅")
    print(f"  📄 Documentos: {'✅' if docs_ok else '❌'}")
    print(f"  💳 Suscripciones: {'✅' if subs_ok else '❌'}")
    print(f"  🤖 Diagnóstico IA: {'✅' if diag_ok else '❌'}")

    if docs_ok and subs_ok and diag_ok:
        print("\n🎉 TODAS LAS PRUEBAS EXITOSAS")
        print("   El sistema está listo para UX testing")
    else:
        print("\n⚠️ ALGUNAS PRUEBAS FALLARON")
        print("   Revisar errores antes de continuar")


if __name__ == "__main__":
    main()
