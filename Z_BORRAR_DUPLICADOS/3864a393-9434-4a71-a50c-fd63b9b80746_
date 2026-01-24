#!/usr/bin/env python
"""
Script para probar el idioma que se muestra en la web
"""

import requests


def probar_idioma_web():
    """Prueba el idioma que se muestra en la página de clientes"""
    print("🌐 PROBANDO IDIOMA EN LA WEB")
    print("=" * 60)

    try:
        # Hacer request a la página de clientes
        response = requests.get("http://127.0.0.1:8000/taller/clientes/")

        if response.status_code == 200:
            content = response.text

            print(f"✅ Página cargada correctamente (Status: {response.status_code})")

            # Buscar textos específicos para determinar el idioma
            textos_espanol = [
                "Gestión de Clientes",
                "Nuevo Cliente",
                "Buscar por nombre o apellido",
                "Acciones",
            ]

            textos_ingles = [
                "Client Management",
                "New Client",
                "Search by name or last name",
                "Actions",
            ]

            print("\n🔍 ANÁLISIS DE CONTENIDO:")

            # Verificar textos en español
            espanol_encontrado = []
            for texto in textos_espanol:
                if texto in content:
                    espanol_encontrado.append(texto)
                    print(f"   ✅ Español encontrado: '{texto}'")

            # Verificar textos en inglés
            ingles_encontrado = []
            for texto in textos_ingles:
                if texto in content:
                    ingles_encontrado.append(texto)
                    print(f"   ✅ Inglés encontrado: '{texto}'")

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

            # Verificar headers de idioma
            content_language = response.headers.get("Content-Language", "No especificado")
            print(f"   • Content-Language header: {content_language}")

            # Buscar información del país
            if "🇺🇸" in content:
                print("   • País detectado: 🇺🇸 USA")
            elif "🇨🇱" in content:
                print("   • País detectado: 🇨🇱 Chile")

            print("\n🎯 CONCLUSIÓN:")
            if idioma_detectado == "🇺🇸 INGLÉS":
                print("   ✅ CORRECTO: USA muestra inglés")
            elif idioma_detectado == "🇪🇸 ESPAÑOL":
                print("   ❌ INCORRECTO: USA muestra español (debería ser inglés)")
            else:
                print("   ⚠️ INDETERMINADO: No se puede determinar el idioma")

        else:
            print(f"❌ Error al cargar la página (Status: {response.status_code})")

    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está corriendo en http://127.0.0.1:8000?")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n✅ PRUEBA COMPLETADA!")


if __name__ == "__main__":
    probar_idioma_web()
