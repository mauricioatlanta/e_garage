#!/usr/bin/env python
"""
Script para preparar el despliegue a producción de eGarage
Ejecuta las tareas necesarias antes de poner en producción
"""
import os
import sys

import django
from django.core.management import call_command


def setup_django():
    """Configura Django con settings de producción"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
    os.environ.setdefault("DEBUG", "0")
    django.setup()


def run_migrations():
    """Ejecuta las migraciones pendientes"""
    print("🔄 Aplicando migraciones...")
    call_command("migrate", verbosity=1)
    print("✅ Migraciones aplicadas correctamente")


def collect_static():
    """Recolecta archivos estáticos"""
    print("🔄 Recolectando archivos estáticos...")
    call_command("collectstatic", verbosity=1, interactive=False)
    print("✅ Archivos estáticos recolectados")


def check_deployment():
    """Ejecuta el check de deployment"""
    print("🔄 Verificando configuración de deployment...")
    call_command("check", "--deploy", verbosity=1)
    print("✅ Check de deployment completado")


def main():
    """Función principal"""
    print("🚀 Preparando eGarage para producción...\n")

    setup_django()

    try:
        run_migrations()
        collect_static()
        check_deployment()

        print("\n🎉 eGarage está listo para producción!")
        print("\n📋 Checklist final:")
        print("   ✅ Variables de entorno configuradas (DJANGO_SETTINGS_MODULE, DEBUG)")
        print("   ✅ ALLOWED_HOSTS actualizado para dominios de producción")
        print("   ✅ CSRF_TRUSTED_ORIGINS configurado")
        print("   ✅ Configuraciones SSL habilitadas")
        print("   ✅ Migraciones aplicadas")
        print("   ✅ Archivos estáticos recolectados")
        print("   ✅ Check de deployment pasado")
        print("\n⚠️  Recordatorios antes de ir a producción:")
        print("   - Verificar que el dominio tiene SSL/HTTPS habilitado")
        print("   - Configurar CompanySettings (IVA/SalesTax, moneda) para cada tenant")
        print("   - Verificar configuración de email en producción")
        print("   - Hacer backup de la base de datos antes del despliegue")

    except Exception as e:
        print(f"❌ Error durante la preparación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
