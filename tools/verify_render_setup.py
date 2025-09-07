#!/usr/bin/env python3
"""
Script de verificación para el setup de Render
Verifica que todos los archivos necesarios estén presentes y configurados correctamente
"""

import sys
from pathlib import Path


def check_file_exists(file_path, description):
    """Verifica que un archivo exista"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NO ENCONTRADO")
        return False

def check_file_content(file_path, required_content, description):
    """Verifica que un archivo contenga contenido específico"""
    if not Path(file_path).exists():
        print(f"❌ {description}: {file_path} - NO ENCONTRADO")
        return False

    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        for item in required_content:
            if item in content:
                print(f"✅ {description}: {item} encontrado en {file_path}")
            else:
                print(f"❌ {description}: {item} NO encontrado en {file_path}")
                return False
        return True
    except Exception as e:
        print(f"❌ {description}: Error leyendo {file_path} - {e}")
        return False

def main():
    print("🔍 Verificando setup para Render...")
    print("=" * 50)

    all_good = True

    # Verificar archivos principales
    files_to_check = [
        ("render.yaml", "Configuración de Render"),
        ("requirements.txt", "Dependencias de Python"),
        ("manage.py", "Script de gestión de Django"),
        ("gestion_taller/wsgi.py", "Configuración WSGI"),
        ("gestion_taller/settings/production.py", "Settings de producción"),
    ]

    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_good = False

    print("\n" + "=" * 50)
    print("🔧 Verificando configuración específica...")

    # Verificar render.yaml
    render_checks = [
        "type: web",
        "env: python",
        "gunicorn",
        "collectstatic",
        "migrate"
    ]

    if not check_file_content("render.yaml", render_checks, "Configuración de Render"):
        all_good = False

    # Verificar requirements.txt
    requirements_checks = [
        "Django>=",
        "psycopg2-binary",
        "dj-database-url",
        "whitenoise",
        "gunicorn"
    ]

    if not check_file_content("requirements.txt", requirements_checks, "Dependencias"):
        all_good = False

    # Verificar production.py
    production_checks = [
        "DEBUG = False",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "dj_database_url.config",
        "STATICFILES_STORAGE",
        "MEDIA_ROOT = Path"
    ]

    if not check_file_content("gestion_taller/settings/production.py", production_checks, "Settings de producción"):
        all_good = False

    print("\n" + "=" * 50)
    print("📁 Verificando estructura de directorios...")

    # Verificar directorios importantes
    dirs_to_check = [
        ("gestion_taller", "Directorio principal del proyecto"),
        ("gestion_taller/settings", "Configuraciones de Django"),
        ("static", "Archivos estáticos"),
        ("media", "Archivos de usuario"),
        ("templates", "Plantillas HTML"),
    ]

    for dir_path, description in dirs_to_check:
        if not check_file_exists(dir_path, description):
            all_good = False

    print("\n" + "=" * 50)

    if all_good:
        print("🎉 ¡Todo está listo para el despliegue en Render!")
        print("\n📋 Próximos pasos:")
        print("1. Ejecuta: python tools/audit_and_cleanup.py --apply")
        print("2. Commit y push a GitHub")
        print("3. Despliega en Render usando el Blueprint")
        return 0
    else:
        print("❌ Hay problemas que deben resolverse antes del despliegue")
        print("\n🔧 Revisa los errores arriba y corrige los archivos faltantes o mal configurados")
        return 1

if __name__ == "__main__":
    sys.exit(main())
