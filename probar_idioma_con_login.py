#!/usr/bin/env python
"""
Script para probar el idioma con login de usuario USA
"""

import re

import requests
from bs4 import BeautifulSoup


def probar_idioma_con_login():
    """Prueba el idioma después de hacer login como usuario USA"""
    print("🌐 PROBANDO IDIOMA CON LOGIN DE USUARIO USA")
    print("=" * 60)

    session = requests.Session()

    try:
        # 1. Obtener la página de login para obtener el CSRF token
        print("1️⃣ Obteniendo página de login...")
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

        # 2. Hacer login como usuario USA
        print("2️⃣ Haciendo login como testuser_usa...")
        login_data = {
            "csrfmiddlewaretoken": csrf_token,
            "login": "testuser_usa",
            "password": "testpass123",
        }

        login_response = session.post(
            "http://127.0.0.1:8000/accounts/login/", data=login_data
        )

        if login_response.status_code == 200 and "login" not in login_response.url:
            print("✅ Login exitoso")
        else:
            print(f"❌ Error en login (Status: {login_response.status_code})")
            print(f"   URL después del login: {login_response.url}")
            return

        # 3. Acceder a la página de clientes
        print("3️⃣ Accediendo a página de clientes...")
        clientes_response = session.get("http://127.0.0.1:8000/taller/clientes/")

        if clientes_response.status_code != 200:
            print(
                f"❌ Error al acceder a clientes (Status: {clientes_response.status_code})"
            )
            return

        print("✅ Página de clientes cargada")

        # 4. Analizar el contenido
        content = clientes_response.text

        print("\n🔍 ANÁLISIS DE CONTENIDO:")

        # Buscar textos específicos
        textos_espanol = [
            "Gestión de Clientes",
            "Nuevo Cliente",
            "Buscar por nombre o apellido",
            "Acciones",
            "Listado inteligente",
        ]

        textos_ingles = [
            "Client Management",
            "New Client",
            "Search by name or last name",
            "Actions",
            "Smart listing",
        ]

        # Verificar textos en español
        espanol_encontrado = []
        for texto in textos_espanol:
            if texto in content:
                espanol_encontrado.append(texto)
                print(f"   ✅ Español: '{texto}'")

        # Verificar textos en inglés
        ingles_encontrado = []
        for texto in textos_ingles:
            if texto in content:
                ingles_encontrado.append(texto)
                print(f"   ✅ Inglés: '{texto}'")

        # Buscar información del país
        if "🇺🇸" in content:
            print("   🌍 País: 🇺🇸 USA")
        elif "🇨🇱" in content:
            print("   🌍 País: 🇨🇱 Chile")

        # Verificar headers
        content_language = clientes_response.headers.get(
            "Content-Language", "No especificado"
        )
        print(f"   📋 Content-Language: {content_language}")

        # Determinar idioma predominante
        if len(espanol_encontrado) > len(ingles_encontrado):
            idioma_detectado = "🇪🇸 ESPAÑOL"
        elif len(ingles_encontrado) > len(espanol_encontrado):
            idioma_detectado = "🇺🇸 INGLÉS"
        else:
            idioma_detectado = "❓ INDETERMINADO"

        print("\n📊 RESULTADO:")
        print(f"   • Textos en español: {len(espanol_encontrado)}")
        print(f"   • Textos en inglés: {len(ingles_encontrado)}")
        print(f"   • Idioma detectado: {idioma_detectado}")

        print("\n🎯 CONCLUSIÓN:")
        if idioma_detectado == "🇺🇸 INGLÉS":
            print("   ✅ CORRECTO: USA muestra inglés")
        elif idioma_detectado == "🇪🇸 ESPAÑOL":
            print("   ❌ INCORRECTO: USA muestra español (debería ser inglés)")
        else:
            print("   ⚠️ INDETERMINADO: No se puede determinar el idioma")

        # Mostrar fragmento del contenido para debug
        print("\n🔍 FRAGMENTO DEL CONTENIDO:")
        soup = BeautifulSoup(content, "html.parser")
        title = soup.find("title")
        if title:
            print(f"   Título: {title.get_text()}")

        # Buscar el primer h1 o h2
        header = soup.find(["h1", "h2"])
        if header:
            print(f"   Encabezado: {header.get_text()}")

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
    probar_idioma_con_login()
