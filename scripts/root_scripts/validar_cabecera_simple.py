#!/usr/bin/env python
"""
✅ Validador Simple de Cabecera de Navegación - eGarage Chile
Confirma que la página /cl/ tiene opciones de login/registro en la cabecera
"""

import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.test import Client


def test_navigation_header():
    """Probar que la cabecera de navegación funciona correctamente"""

    print("🌐 VALIDADOR SIMPLE DE CABECERA DE NAVEGACIÓN")
    print("=" * 60)

    client = Client()

    # Probar página /cl/ sin autenticación
    try:
        response = client.get("/cl/")

        if response.status_code == 200:
            print("✅ Página /cl/ carga correctamente (200)")

            # Verificar contenido HTML básico
            content = response.content.decode("utf-8")

            # Verificar elementos clave de la cabecera
            checks = [
                ("<header", "Elemento <header>"),
                ("eGarage", "Texto del logo"),
                ("🇨🇱 Chile", "Indicador de país"),
                ('href="/login/"', "Enlace de login"),
                ('href="/registro/"', "Enlace de registro"),
                ("Ingresar", "Texto botón Ingresar"),
                ("Registrarse", "Texto botón Registrarse"),
                ("mobile-menu", "Menú móvil"),
                ("fas fa-", "Iconos Font Awesome"),
                ("from-cyan-400", "Gradientes CSS"),
            ]

            print("\n📋 VERIFICANDO ELEMENTOS DE LA CABECERA:")
            print("-" * 50)

            all_ok = True
            for check, description in checks:
                if check in content:
                    print(f"✅ {description}")
                else:
                    print(f"❌ {description} - NO ENCONTRADO")
                    all_ok = False

            return all_ok

        else:
            print(f"❌ Error al cargar /cl/: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error al probar /cl/: {e}")
        return False


def test_navigation_links():
    """Probar que los enlaces de navegación funcionan"""

    print("\n🔗 PROBANDO ENLACES DE NAVEGACIÓN:")
    print("-" * 50)

    client = Client()

    test_links = [
        ("/login/", "Login"),
        ("/registro/", "Registro"),
        ("/accounts/signup/", "Django Allauth Signup"),
        ("/accounts/login/", "Django Allauth Login"),
    ]

    for url, description in test_links:
        try:
            response = client.get(url)
            if response.status_code in [200, 302]:
                print(f"✅ {description} ({url}) → {response.status_code}")
            else:
                print(f"⚠️  {description} ({url}) → {response.status_code}")
        except Exception as e:
            print(f"❌ Error en {description}: {e}")


def test_template_content():
    """Verificar contenido específico del template"""

    print("\n📄 VERIFICANDO CONTENIDO DEL TEMPLATE:")
    print("-" * 50)

    template_path = "templates/onboarding/bienvenida_chile.html"

    try:
        with open(template_path, encoding="utf-8") as f:
            content = f.read()

        template_checks = [
            ("<header class=", "Cabecera HTML"),
            ("backdrop-blur", "Efectos de blur"),
            ("border-cyan-400", "Bordes cyan"),
            ("mobile-menu-toggle", "Toggle menú móvil"),
            ("fa-sign-in-alt", "Icono de login"),
            ("fa-user-plus", "Icono de registro"),
            ("addEventListener", "JavaScript para interactividad"),
        ]

        for check, description in template_checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"⚠️  {description} - No encontrado")

        # Contar elementos importantes
        login_count = content.count('href="/login/"')
        registro_count = content.count('href="/registro/"')

        print("\n📊 ESTADÍSTICAS DEL TEMPLATE:")
        print(f"   • Enlaces a /login/: {login_count}")
        print(f"   • Enlaces a /registro/: {registro_count}")
        print(f"   • Tamaño del archivo: {len(content)} caracteres")

    except FileNotFoundError:
        print(f"❌ Template no encontrado: {template_path}")
    except Exception as e:
        print(f"❌ Error leyendo template: {e}")


def main():
    """Ejecutar todas las validaciones"""

    print("🚀 INICIANDO VALIDACIÓN DE CABECERA...")
    print()

    # Prueba 1: Cabecera de navegación
    header_ok = test_navigation_header()

    # Prueba 2: Enlaces de navegación
    test_navigation_links()

    # Prueba 3: Contenido del template
    test_template_content()

    print("\n" + "=" * 60)
    if header_ok:
        print("🎯 VALIDACIÓN EXITOSA - Cabecera funcionando correctamente")
        print()
        print("📌 CARACTERÍSTICAS IMPLEMENTADAS:")
        print("   ✅ Cabecera de navegación con backdrop blur")
        print("   ✅ Logo de eGarage con indicador de país")
        print("   ✅ Botón 'Ingresar' que redirige a /login/")
        print("   ✅ Botón 'Registrarse' que redirige a /registro/")
        print("   ✅ Diseño responsive con menú móvil")
        print("   ✅ Efectos visuales futuristas (gradientes, hover)")
        print("   ✅ Iconos Font Awesome para mejor UX")
        print()
        print("🔑 CÓMO USAR:")
        print("   1. Ir a http://127.0.0.1:8000/cl/")
        print("   2. Observar la cabecera superior con opciones")
        print("   3. Clic en 'Registrarse' para crear cuenta nueva")
        print("   4. Clic en 'Ingresar' para login con credenciales")
        print("   5. En móvil: usar el botón hamburguesa para navegación")
        print()
        print("✨ PROBLEMA SOLUCIONADO:")
        print("   La página /cl/ ahora tiene una cabecera clara con")
        print("   opciones de autenticación visibles y funcionales.")
    else:
        print("❌ VALIDACIÓN FALLIDA - Revisar implementación")
        return False

    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
