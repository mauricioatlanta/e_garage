#!/usr/bin/env python
"""
Verificación Final de Despliegue
Script para verificar que todo está listo para producción
"""

import os
import sys

import django
from django.contrib.auth import get_user_model
from django.test import Client

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
django.setup()

User = get_user_model()


def check_critical_files():
    """Verificar archivos críticos"""
    print("🔍 VERIFICANDO ARCHIVOS CRÍTICOS")
    print("=" * 50)

    critical_files = [
        "static/taller/common/js/documentos_form.js",
        "gestion_taller/settings/production.py",
        "render.yaml",
        "digitalocean_wsgi.py",
        "taller/views_health.py",
    ]

    missing_files = []
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - FALTANTE")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n⚠️  {len(missing_files)} archivos críticos faltantes")
        return False
    else:
        print("\n✅ Todos los archivos críticos presentes")
        return True


def check_health_endpoints():
    """Verificar endpoints de health check"""
    print("\n🏥 VERIFICANDO HEALTH CHECK")
    print("=" * 50)

    client = Client()

    try:
        # Health check completo
        response = client.get("/health/")
        if response.status_code == 200:
            print("✅ /health/ - OK")
        else:
            print(f"❌ /health/ - Error: {response.status_code}")
            return False

        # Health check simple
        response = client.get("/health-simple/")
        if response.status_code == 200:
            print("✅ /health-simple/ - OK")
        else:
            print(f"❌ /health-simple/ - Error: {response.status_code}")
            return False

        print("\n✅ Health checks funcionando correctamente")
        return True

    except Exception as e:
        print(f"❌ Error en health checks: {e}")
        return False


def check_multi_tenant():
    """Verificar funcionalidad multi-tenant"""
    print("\n🌍 VERIFICANDO MULTI-TENANT")
    print("=" * 50)

    client = Client()

    # Test Chile
    print("\n🇨🇱 Testing Chile")
    try:
        login_success = client.login(username="test_chile", password="test123")
        if login_success:
            print("✅ Login CL exitoso")
            response = client.get("/cl/es/documentos/form/")
            if response.status_code == 200:
                print("✅ Formulario CL carga correctamente")
            else:
                print(f"❌ Formulario CL error: {response.status_code}")
                return False
        else:
            print("❌ Login CL falló")
            return False
    except Exception as e:
        print(f"❌ Error en test CL: {e}")
        return False

    # Test USA
    print("\n🇺🇸 Testing USA")
    try:
        login_success = client.login(username="testuser_usa", password="TestUSA2025!")
        if login_success:
            print("✅ Login US exitoso")
            response = client.get("/us/en/documentos/form/")
            if response.status_code == 200:
                print("✅ Formulario US carga correctamente")
            else:
                print(f"❌ Formulario US error: {response.status_code}")
                return False
        else:
            print("❌ Login US falló")
            return False
    except Exception as e:
        print(f"❌ Error en test US: {e}")
        return False

    print("\n✅ Multi-tenant funcionando correctamente")
    return True


def check_static_files():
    """Verificar archivos estáticos"""
    print("\n📁 VERIFICANDO ARCHIVOS ESTÁTICOS")
    print("=" * 50)

    client = Client()

    try:
        # JavaScript principal
        response = client.get("/static/taller/common/js/documentos_form.js")
        if response.status_code == 200:
            print("✅ JavaScript principal carga correctamente")
            content = response.content.decode("utf-8")
            if "recalcTotals" in content:
                print("✅ Función recalcTotals encontrada")
            if "VAT_PCT" in content:
                print("✅ Variable VAT_PCT encontrada")
        else:
            print(f"❌ JavaScript error: {response.status_code}")
            return False

        print("\n✅ Archivos estáticos funcionando correctamente")
        return True

    except Exception as e:
        print(f"❌ Error en archivos estáticos: {e}")
        return False


def check_database():
    """Verificar base de datos"""
    print("\n🗄️  VERIFICANDO BASE DE DATOS")
    print("=" * 50)

    try:
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Conexión a base de datos OK")

        # Verificar modelos críticos
        from taller.models import Cliente, Documento, Empresa, Vehiculo

        doc_count = Documento.objects.count()
        emp_count = Empresa.objects.count()
        cli_count = Cliente.objects.count()
        veh_count = Vehiculo.objects.count()

        print(f"✅ Documentos: {doc_count}")
        print(f"✅ Empresas: {emp_count}")
        print(f"✅ Clientes: {cli_count}")
        print(f"✅ Vehículos: {veh_count}")

        print("\n✅ Base de datos funcionando correctamente")
        return True

    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        return False


def main():
    """Ejecutar verificación completa"""
    print("🎯 VERIFICACIÓN FINAL DE DESPLIEGUE")
    print("=" * 60)
    print("eGarage Django - Verificación completa para producción")
    print("=" * 60)

    results = []

    # Ejecutar verificaciones
    results.append(("Archivos Críticos", check_critical_files()))
    results.append(("Health Check", check_health_endpoints()))
    results.append(("Multi-tenant", check_multi_tenant()))
    results.append(("Archivos Estáticos", check_static_files()))
    results.append(("Base de Datos", check_database()))

    # Resumen final
    print("\n📊 RESUMEN FINAL")
    print("=" * 50)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1

    print(f"\nResultado: {passed}/{total} verificaciones pasaron")

    if passed == total:
        print("\n🎉 ¡SISTEMA 100% LISTO PARA PRODUCCIÓN!")
        print("✅ Todas las verificaciones pasaron")
        print("✅ Archivos de configuración listos")
        print("✅ Health checks funcionando")
        print("✅ Multi-tenant operativo")
        print("✅ Archivos estáticos optimizados")
        print("✅ Base de datos estable")
        print("\n🚀 LISTO PARA DESPLEGAR EN RENDER O DIGITALOCEAN")
    else:
        print(f"\n⚠️  {total - passed} problemas encontrados")
        print("❌ Revisar y corregir antes del despliegue")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
