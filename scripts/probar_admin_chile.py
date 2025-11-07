#!/usr/bin/env python
"""
Script para probar con admin (que tiene empresa de Chile según los logs)
"""

import re

import requests


def probar_admin_chile():
    """Prueba con admin (usuario que debería mostrar Chile)"""
    print("🇨🇱 PROBANDO CON ADMIN (CHILE)")
    print("=" * 60)

    session = requests.Session()

    try:
        # 1. Limpiar cookies
        session.cookies.clear()
        print("1️⃣ Cookies limpiadas")

        # 2. Obtener página de login
        print("2️⃣ Obteniendo página de login...")
        login_page = session.get("http://127.0.0.1:8000/accounts/login/")

        if login_page.status_code != 200:
            print(
                f"❌ Error al obtener página de login (Status: {login_page.status_code})"
            )
            return

        # Extraer CSRF token
        csrf_match = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text
        )
        if not csrf_match:
            print("❌ No se encontró CSRF token")
            return

        csrf_token = csrf_match.group(1)
        print("✅ CSRF token obtenido")

        # 3. Hacer login como admin
        print("3️⃣ Haciendo login como admin...")
        login_data = {
            "csrfmiddlewaretoken": csrf_token,
            "login": "admin",
            "password": "admin123",
        }

        login_response = session.post(
            "http://127.0.0.1:8000/accounts/login/", data=login_data
        )

        if login_response.status_code == 200 and "login" not in login_response.url:
            print("✅ Login exitoso como admin")
        else:
            print(f"❌ Error en login (Status: {login_response.status_code})")
            print(f"   URL después del login: {login_response.url}")
            return

        # 4. Acceder a la página de clientes
        print("4️⃣ Accediendo a página de clientes...")
        clientes_response = session.get("http://127.0.0.1:8000/taller/clientes/")

        if clientes_response.status_code != 200:
            print(
                f"❌ Error al acceder a clientes (Status: {clientes_response.status_code})"
            )
            return

        print("✅ Página de clientes cargada")

        # 5. Analizar el contenido
        content = clientes_response.text

        print("\n🔍 ANÁLISIS DE BOTONES DE NAVEGACIÓN:")

        # Buscar botones de navegación específicos
        botones_espanol = [
            "Clientes",
            "Vehículos",
            "Repuestos",
            "Servicios",
            "Documentos",
        ]

        botones_ingles = ["Clients", "Vehicles", "Parts", "Services", "Documents"]

        # Verificar botones en español
        espanol_encontrado = []
        for boton in botones_espanol:
            if boton in content:
                espanol_encontrado.append(boton)
                print(f"   ✅ Español: '{boton}'")

        # Verificar botones en inglés
        ingles_encontrado = []
        for boton in botones_ingles:
            if boton in content:
                ingles_encontrado.append(boton)
                print(f"   ✅ Inglés: '{boton}'")

        # Verificar headers
        content_language = clientes_response.headers.get(
            "Content-Language", "No especificado"
        )
        print(f"   📋 Content-Language: {content_language}")

        # Buscar información del país
        if "🇺🇸" in content:
            print("   🌍 País detectado: 🇺🇸 USA")
        elif "🇨🇱" in content:
            print("   🌍 País detectado: 🇨🇱 Chile")

        # Determinar idioma predominante
        if len(espanol_encontrado) > len(ingles_encontrado):
            idioma_detectado = "🇪🇸 ESPAÑOL"
        elif len(ingles_encontrado) > len(espanol_encontrado):
            idioma_detectado = "🇺🇸 INGLÉS"
        else:
            idioma_detectado = "❓ INDETERMINADO"

        print("\n📊 RESULTADO:")
        print(f"   • Botones en español: {len(espanol_encontrado)}")
        print(f"   • Botones en inglés: {len(ingles_encontrado)}")
        print(f"   • Idioma detectado: {idioma_detectado}")
        print(f"   • Content-Language: {content_language}")

        print("\n🎯 CONCLUSIÓN:")
        if idioma_detectado == "🇪🇸 ESPAÑOL":
            print("   ✅ CORRECTO: Chile muestra español")
        elif idioma_detectado == "🇺🇸 INGLÉS":
            print("   ❌ INCORRECTO: Chile muestra inglés (debería ser español)")
            print("   🔧 PROBLEMA: Los botones de navegación están en inglés")
        else:
            print("   ⚠️ INDETERMINADO: No se puede determinar el idioma")

    except requests.exceptions.ConnectionError:
        print(
            "❌ No se puede conectar al servidor. ¿Está corriendo en http://127.0.0.1:8000?"
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    print("\n✅ PRUEBA COMPLETADA!")


if __name__ == "__main__":
    probar_admin_chile()
