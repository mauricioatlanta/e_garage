#!/usr/bin/env python
"""
Script de diagnóstico automatizado para eGarage
Identifica problemas de imports y configuración
"""

import importlib
import os
import sys
import traceback
from pathlib import Path


def setup_django():
    """Configurar Django para diagnóstico"""
    # Agregar el directorio del proyecto al path
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
    os.environ.setdefault("EGARAGE_SAFE_MODE", "1")

    try:
        import django

        django.setup()
        return True
    except Exception as e:
        print(f"❌ Error configurando Django: {e}")
        return False


def test_import_chain(module_path):
    """Probar cadena de imports específica"""
    try:
        print(f"🔍 Probando import: {module_path}")
        importlib.import_module(module_path)
        print(f"✅ OK: {module_path}")
        return True
    except Exception as e:
        print(f"❌ ERROR en {module_path}: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False


def diagnose_urls():
    """Diagnosticar problemas en URLs"""
    print("\n" + "=" * 60)
    print("🔍 DIAGNÓSTICO DE URLs")
    print("=" * 60)

    # Probar imports específicos problemáticos
    problematic_imports = [
        "gestion_taller.urls",
        "taller.views.country_aware_auth",
        "taller.views_extra.login_redirector",
        "taller.views_extra.suscripcion",
        "taller.views_extra.views_trial",
        "taller.views_extra.views_trial_activate",
    ]

    results = {}
    for module in problematic_imports:
        results[module] = test_import_chain(module)

    return results


def diagnose_settings():
    """Diagnosticar configuración"""
    print("\n" + "=" * 60)
    print("🔍 DIAGNÓSTICO DE SETTINGS")
    print("=" * 60)

    try:
        from django.conf import settings

        print("✅ Settings cargados correctamente")
        print(f"   ROOT_URLCONF: {settings.ROOT_URLCONF}")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   SAFE_MODE: {getattr(settings, 'SAFE_MODE', 'No definido')}")
        return True
    except Exception as e:
        print(f"❌ Error cargando settings: {e}")
        return False


def diagnose_models():
    """Diagnosticar modelos"""
    print("\n" + "=" * 60)
    print("🔍 DIAGNÓSTICO DE MODELOS")
    print("=" * 60)

    try:
        from django.apps import apps

        print("✅ Apps registry listo")
        print(f"   Apps instaladas: {len(apps.get_app_configs())}")

        # Probar algunos modelos específicos
        test_models = [
            "taller.models.empresa.Empresa",
            "taller.models.trial.TrialRegistro",
        ]

        for model_path in test_models:
            try:
                app_label, model_name = model_path.split(".")[-2:]
                model = apps.get_model(app_label, model_name)
                print(f"✅ Modelo {model_path} OK")
            except Exception as e:
                print(f"❌ Error en modelo {model_path}: {e}")

        return True
    except Exception as e:
        print(f"❌ Error en apps registry: {e}")
        return False


def main():
    """Función principal de diagnóstico"""
    print("🚀 DIAGNÓSTICO AUTOMATIZADO DE EGARAGE")
    print("=" * 60)

    # Cambiar al directorio del proyecto
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)
    print(f"📁 Directorio de trabajo: {project_root}")

    # Configurar Django
    if not setup_django():
        print("❌ No se pudo configurar Django. Abortando.")
        return 1

    # Ejecutar diagnósticos
    settings_ok = diagnose_settings()
    models_ok = diagnose_models()
    urls_results = diagnose_urls()

    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)

    print(f"Settings: {'✅ OK' if settings_ok else '❌ ERROR'}")
    print(f"Modelos: {'✅ OK' if models_ok else '❌ ERROR'}")

    urls_ok = all(urls_results.values())
    print(f"URLs: {'✅ OK' if urls_ok else '❌ ERRORES'}")

    if not urls_ok:
        print("\n❌ Módulos con problemas:")
        for module, ok in urls_results.items():
            if not ok:
                print(f"   - {module}")

    # Recomendaciones
    print("\n" + "=" * 60)
    print("💡 RECOMENDACIONES")
    print("=" * 60)

    if not urls_ok:
        print("1. Mover imports de modelos dentro de las funciones")
        print("2. Evitar imports a nivel de módulo que dependan de Django apps")
        print("3. Usar lazy imports o imports condicionales")

    if settings_ok and models_ok and urls_ok:
        print("🎉 ¡Sistema funcionando correctamente!")
        print("   Puedes ejecutar: python manage.py check")
        return 0
    else:
        print("⚠️  Se encontraron problemas que requieren atención")
        return 1


if __name__ == "__main__":
    sys.exit(main())
