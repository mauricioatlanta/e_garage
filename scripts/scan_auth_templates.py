#!/usr/bin/env python3
"""
Script para escanear templates de autenticación y verificar cuáles están activos.
"""

import argparse
import glob
import os


def scan_filesystem_templates():
    """Escanea el filesystem buscando templates de auth."""
    print("🔍 ESCANEANDO TEMPLATES DE AUTENTICACIÓN EN FILESYSTEM")
    print("=" * 60)

    # Patrones a buscar
    patterns = [
        "**/login*.html",
        "**/signup*.html",
        "**/auth*.html",
        "**/account*.html",
        "**/password*.html",
        "**/email*.html",
    ]

    found_templates = {}

    for pattern in patterns:
        files = glob.glob(pattern, recursive=True)
        if files:
            category = pattern.replace("**/", "").replace("*.html", "")
            found_templates[category] = files

    # Mostrar resultados
    total = 0
    for category, files in found_templates.items():
        print(f"\n📁 {category.upper()}: {len(files)} archivos")
        for file in sorted(files):
            print(f"   {file}")
            total += 1

    print(f"\n📊 TOTAL ENCONTRADO: {total} templates de autenticación")
    return found_templates


def scan_django_templates():
    """Escanea usando Django para ver qué templates se resuelven realmente."""
    print("\n🐍 ESCANEANDO CON DJANGO (RESOLUCIÓN REAL)")
    print("=" * 60)

    try:
        import django
        from django.conf import settings
        from django.template.exceptions import TemplateDoesNotExist
        from django.template.loader import get_template

        # Configurar Django
        if not settings.configured:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
            django.setup()

        # Templates a verificar
        templates_to_check = [
            "account/login.html",
            "account/signup.html",
            "account/logout.html",
            "account/password_reset.html",
            "account/email_confirm.html",
            "registration/login.html",
            "registration/signup.html",
        ]

        print("🔍 Verificando resolución de templates:")
        for template_name in templates_to_check:
            try:
                template = get_template(template_name)
                origin = getattr(template, "origin", None)
                if origin:
                    print(f"✅ {template_name:<25} → {origin.name}")
                else:
                    print(f"✅ {template_name:<25} → Resuelto (sin origin)")
            except TemplateDoesNotExist:
                print(f"❌ {template_name:<25} → No encontrado")
            except Exception as e:
                print(f"⚠️  {template_name:<25} → Error: {e}")

    except ImportError:
        print("❌ Django no disponible. Ejecuta con --django para usar resolución real.")
    except Exception as e:
        print(f"❌ Error configurando Django: {e}")


def check_template_override():
    """Verifica si existe el override de login."""
    print("\n🎯 VERIFICANDO OVERRIDE DE LOGIN")
    print("=" * 60)

    override_paths = [
        "templates/account/login.html",
        "templates/account/login_futuristic.html",
    ]

    for path in override_paths:
        if os.path.exists(path):
            print(f"✅ {path} - EXISTE")
            # Mostrar primeras líneas
            try:
                with open(path, encoding="utf-8") as f:
                    lines = f.readlines()[:5]
                    print("   Primeras líneas:")
                    for i, line in enumerate(lines, 1):
                        print(f"   {i}: {line.strip()}")
            except Exception as e:
                print(f"   Error leyendo archivo: {e}")
        else:
            print(f"❌ {path} - NO EXISTE")


def main():
    parser = argparse.ArgumentParser(description="Escanea templates de autenticación")
    parser.add_argument("--django", action="store_true", help="Usar resolución real de Django")

    args = parser.parse_args()

    # Escanear filesystem
    scan_filesystem_templates()

    # Verificar override
    check_template_override()

    # Escanear con Django si se solicita
    if args.django:
        scan_django_templates()
    else:
        print("\n💡 Para ver resolución real de Django, ejecuta:")
        print("   python scan_auth_templates.py --django")


if __name__ == "__main__":
    main()
