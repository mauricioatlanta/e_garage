#!/usr/bin/env python3
"""
Test web completo con autenticación
"""
import os

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

print("🌐 === TEST WEB COMPLETO ===")

# Configurar sesión simple
session = requests.Session()

BASE_URL = "http://127.0.0.1:8000"

try:
    # 1. Verificar que el servidor responde
    print("🔍 1. Verificando servidor...")
    response = session.get(f"{BASE_URL}/", timeout=10)
    print(f"   Status: {response.status_code}")

    # 2. Obtener página de login
    print("🔑 2. Obteniendo página de login...")
    login_page = session.get(f"{BASE_URL}/accounts/login/", timeout=10)
    print(f"   Status: {login_page.status_code}")

    # Extraer CSRF token
    import re

    csrf_match = re.search(
        r'name="csrfmiddlewaretoken" value="([^"]*)"', login_page.text
    )
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"   ✅ CSRF token obtenido: {csrf_token[:10]}...")

        # 3. Hacer login
        print("🚀 3. Haciendo login...")
        login_data = {
            "csrfmiddlewaretoken": csrf_token,
            "login": "admin",
            "password": "admin123",
        }

        login_response = session.post(
            f"{BASE_URL}/accounts/login/",
            data=login_data,
            headers={"Referer": f"{BASE_URL}/accounts/login/"},
            timeout=10,
            allow_redirects=False,  # No seguir redirects automáticamente
        )
        print(f"   Status: {login_response.status_code}")

        if (
            login_response.status_code in [200, 302]
            and "admin" in session.get(f"{BASE_URL}/").text
        ):
            print("   ✅ Login exitoso")

            # 4. Acceder al dashboard
            print("📊 4. Accediendo al dashboard...")
            dashboard = session.get(f"{BASE_URL}/dashboard/", timeout=10)
            print(f"   Status: {dashboard.status_code}")

            # 5. Acceder a crear documento
            print("📄 5. Accediendo a crear documento...")
            crear_doc = session.get(f"{BASE_URL}/documentos/nuevo/", timeout=10)
            print(f"   Status: {crear_doc.status_code}")

            if crear_doc.status_code == 200:
                print("   ✅ Página de crear documento accessible")

                # 6. Intentar editar un documento existente
                print("✏️ 6. Intentando editar documento 40...")
                editar_doc = session.get(
                    f"{BASE_URL}/documentos/editar/40/", timeout=10
                )
                print(f"   Status: {editar_doc.status_code}")

                if editar_doc.status_code == 200:
                    print("   ✅ Página de editar documento accessible")
                elif editar_doc.status_code == 404:
                    print("   ⚠️ Documento 40 no existe")
                else:
                    print("   ❌ Error al acceder a editar documento")
                    print(f"   Response: {editar_doc.text[:200]}")
            else:
                print("   ❌ Error al acceder a crear documento")
                print(f"   Response: {crear_doc.text[:200]}")
        else:
            print("   ❌ Error en login")
            print(f"   Response: {login_response.text[:200]}")
    else:
        print("   ❌ No se pudo obtener CSRF token")
        print(f"   Page content: {login_page.text[:200]}")

except requests.exceptions.ConnectionError:
    print("❌ Error: No se puede conectar al servidor")
    print("   Verifica que el servidor Django esté corriendo en http://127.0.0.1:8000")
except requests.exceptions.Timeout:
    print("❌ Error: Timeout al conectar con el servidor")
except Exception as e:
    print(f"❌ Error inesperado: {e}")

print("\n🏁 === FIN TEST WEB ===")
