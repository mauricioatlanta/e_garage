#!/usr/bin/env python
"""
Script de verificación post-deployment para eGarage
Verifica que todas las configuraciones de seguridad estén funcionando
"""
import os
import sys

import django
from django.conf import settings


def setup_django():
    """Configura Django con settings de producción"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
    os.environ.setdefault("DEBUG", "0")
    django.setup()


def verify_security_settings():
    """Verifica las configuraciones de seguridad"""
    print("🔒 Verificando configuraciones de seguridad...\n")

    checks = []

    # Verificar DEBUG
    debug_status = "✅" if not settings.DEBUG else "❌"
    checks.append(f"{debug_status} DEBUG = {settings.DEBUG}")

    # Verificar ALLOWED_HOSTS
    allowed_hosts_ok = (
        len(settings.ALLOWED_HOSTS) > 0 and "*" not in settings.ALLOWED_HOSTS
    )
    hosts_status = "✅" if allowed_hosts_ok else "❌"
    checks.append(f"{hosts_status} ALLOWED_HOSTS = {settings.ALLOWED_HOSTS}")

    # Verificar SSL
    ssl_status = "✅" if settings.SECURE_SSL_REDIRECT else "❌"
    checks.append(f"{ssl_status} SECURE_SSL_REDIRECT = {settings.SECURE_SSL_REDIRECT}")

    # Verificar cookies seguras
    cookies_status = "✅" if settings.SESSION_COOKIE_SECURE else "❌"
    checks.append(
        f"{cookies_status} SESSION_COOKIE_SECURE = {settings.SESSION_COOKIE_SECURE}"
    )

    # Verificar CSRF
    csrf_status = "✅" if settings.CSRF_COOKIE_SECURE else "❌"
    checks.append(f"{csrf_status} CSRF_COOKIE_SECURE = {settings.CSRF_COOKIE_SECURE}")

    # Verificar HSTS
    hsts_status = "✅" if settings.SECURE_HSTS_SECONDS > 0 else "❌"
    checks.append(f"{hsts_status} SECURE_HSTS_SECONDS = {settings.SECURE_HSTS_SECONDS}")

    # Verificar CSRF_TRUSTED_ORIGINS
    csrf_origins_ok = len(settings.CSRF_TRUSTED_ORIGINS) > 0
    origins_status = "✅" if csrf_origins_ok else "❌"
    checks.append(f"{origins_status} CSRF_TRUSTED_ORIGINS configurado")

    # Verificar X-Frame-Options
    xframe_status = "✅" if hasattr(settings, "X_FRAME_OPTIONS") else "❌"
    checks.append(
        f"{xframe_status} X_FRAME_OPTIONS = {getattr(settings, 'X_FRAME_OPTIONS', 'NO CONFIGURADO')}"
    )

    for check in checks:
        print(check)

    # Contar errores
    errors = sum(1 for check in checks if check.startswith("❌"))

    if errors == 0:
        print("\n🎉 ¡Todas las configuraciones de seguridad están correctas!")
        return True
    else:
        print(f"\n⚠️  Se encontraron {errors} problemas de configuración.")
        return False


def verify_database():
    """Verifica la conectividad de la base de datos"""
    print("\n🗄️  Verificando base de datos...")
    try:
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Conexión a base de datos exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {e}")
        return False


def verify_static_files():
    """Verifica la configuración de archivos estáticos"""
    print("\n📁 Verificando archivos estáticos...")
    try:
        static_root = settings.STATIC_ROOT
        if static_root and os.path.exists(static_root):
            file_count = sum(len(files) for _, _, files in os.walk(static_root))
            print(f"✅ STATIC_ROOT configurado: {static_root}")
            print(f"✅ Archivos estáticos encontrados: {file_count}")
            return True
        else:
            print("❌ STATIC_ROOT no configurado o no existe")
            return False
    except Exception as e:
        print(f"❌ Error verificando archivos estáticos: {e}")
        return False


def main():
    """Función principal"""
    print("🔍 Verificación Post-Deployment eGarage\n")
    print("=" * 50)

    setup_django()

    # Ejecutar verificaciones
    security_ok = verify_security_settings()
    db_ok = verify_database()
    static_ok = verify_static_files()

    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)

    if security_ok and db_ok and static_ok:
        print("🎉 ¡eGarage está listo para producción!")
        print("\n✅ Todas las verificaciones pasaron exitosamente")
        print("\n🚀 Puedes proceder con el deployment")
    else:
        print("⚠️  Se encontraron problemas que deben resolverse antes del deployment")
        print("\n📋 Problemas encontrados:")
        if not security_ok:
            print("   - Configuraciones de seguridad incompletas")
        if not db_ok:
            print("   - Problemas de conectividad de base de datos")
        if not static_ok:
            print("   - Problemas con archivos estáticos")

        print("\n❌ Deployment NO recomendado en este momento")
        sys.exit(1)


if __name__ == "__main__":
    main()
