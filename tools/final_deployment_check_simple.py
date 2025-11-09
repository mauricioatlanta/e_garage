#!/usr/bin/env python
"""
Verificacion Final de Despliegue
Script para verificar que todo esta listo para produccion
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
    """Verificar archivos criticos"""
    print("VERIFICANDO ARCHIVOS CRITICOS")
    print("=" * 50)

    critical_files = [
        "static/taller/common/js/documentos_form.js",
        "gestion_taller/settings/production.py",
        "render.yaml",
        "pythonanywhere_wsgi.py",
        "taller/views_health.py",
    ]

    missing_files = []
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"OK: {file_path}")
        else:
            print(f"ERROR: {file_path} - FALTANTE")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n{len(missing_files)} archivos criticos faltantes")
        return False
    else:
        print("\nTodos los archivos criticos presentes")
        return True


def check_health_endpoints():
    """Verificar endpoints de health check"""
    print("\nVERIFICANDO HEALTH CHECK")
    print("=" * 50)

    client = Client()

    try:
        # Health check completo
        response = client.get("/health/")
        if response.status_code == 200:
            print("OK: /health/ - OK")
        else:
            print(f"ERROR: /health/ - Error: {response.status_code}")
            return False

        # Health check simple
        response = client.get("/health-simple/")
        if response.status_code == 200:
            print("OK: /health-simple/ - OK")
        else:
            print(f"ERROR: /health-simple/ - Error: {response.status_code}")
            return False

        print("\nHealth checks funcionando correctamente")
        return True

    except Exception as e:
        print(f"ERROR: Error en health checks: {e}")
        return False


def check_multi_tenant():
    """Verificar funcionalidad multi-tenant"""
    print("\nVERIFICANDO MULTI-TENANT")
    print("=" * 50)

    client = Client()

    # Test Chile
    print("\nTesting Chile")
    try:
        login_success = client.login(username="test_chile", password="test123")
        if login_success:
            print("OK: Login CL exitoso")
            response = client.get("/cl/es/documentos/form/")
            if response.status_code == 200:
                print("OK: Formulario CL carga correctamente")
            else:
                print(f"ERROR: Formulario CL error: {response.status_code}")
                return False
        else:
            print("ERROR: Login CL fallo")
            return False
    except Exception as e:
        print(f"ERROR: Error en test CL: {e}")
        return False

    # Test USA
    print("\nTesting USA")
    try:
        login_success = client.login(username="testuser_usa", password="TestUSA2025!")
        if login_success:
            print("OK: Login US exitoso")
            response = client.get("/us/en/documentos/form/")
            if response.status_code == 200:
                print("OK: Formulario US carga correctamente")
            else:
                print(f"ERROR: Formulario US error: {response.status_code}")
                return False
        else:
            print("ERROR: Login US fallo")
            return False
    except Exception as e:
        print(f"ERROR: Error en test US: {e}")
        return False

    print("\nMulti-tenant funcionando correctamente")
    return True


def check_static_files():
    """Verificar archivos estaticos"""
    print("\nVERIFICANDO ARCHIVOS ESTATICOS")
    print("=" * 50)

    client = Client()

    try:
        # JavaScript principal
        response = client.get("/static/taller/common/js/documentos_form.js")
        if response.status_code == 200:
            print("OK: JavaScript principal carga correctamente")
            content = response.content.decode("utf-8")
            if "recalcTotals" in content:
                print("OK: Funcion recalcTotals encontrada")
            if "VAT_PCT" in content:
                print("OK: Variable VAT_PCT encontrada")
        else:
            print(f"ERROR: JavaScript error: {response.status_code}")
            return False

        print("\nArchivos estaticos funcionando correctamente")
        return True

    except Exception as e:
        print(f"ERROR: Error en archivos estaticos: {e}")
        return False


def check_database():
    """Verificar base de datos"""
    print("\nVERIFICANDO BASE DE DATOS")
    print("=" * 50)

    try:
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("OK: Conexion a base de datos OK")

        # Verificar modelos criticos
        from taller.models import Cliente, Documento, Empresa, Vehiculo

        doc_count = Documento.objects.count()
        emp_count = Empresa.objects.count()
        cli_count = Cliente.objects.count()
        veh_count = Vehiculo.objects.count()

        print(f"OK: Documentos: {doc_count}")
        print(f"OK: Empresas: {emp_count}")
        print(f"OK: Clientes: {cli_count}")
        print(f"OK: Vehiculos: {veh_count}")

        print("\nBase de datos funcionando correctamente")
        return True

    except Exception as e:
        print(f"ERROR: Error en base de datos: {e}")
        return False


def main():
    """Ejecutar verificacion completa"""
    print("VERIFICACION FINAL DE DESPLIEGUE")
    print("=" * 60)
    print("eGarage Django - Verificacion completa para produccion")
    print("=" * 60)

    results = []

    # Ejecutar verificaciones
    results.append(("Archivos Criticos", check_critical_files()))
    results.append(("Health Check", check_health_endpoints()))
    results.append(("Multi-tenant", check_multi_tenant()))
    results.append(("Archivos Estaticos", check_static_files()))
    results.append(("Base de Datos", check_database()))

    # Resumen final
    print("\nRESUMEN FINAL")
    print("=" * 50)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1

    print(f"\nResultado: {passed}/{total} verificaciones pasaron")

    if passed == total:
        print("\nSISTEMA 100% LISTO PARA PRODUCCION!")
        print("Todas las verificaciones pasaron")
        print("Archivos de configuracion listos")
        print("Health checks funcionando")
        print("Multi-tenant operativo")
        print("Archivos estaticos optimizados")
        print("Base de datos estable")
        print("\nLISTO PARA DESPLEGAR EN RENDER O PYTHONANYWHERE")
    else:
        print(f"\n{total - passed} problemas encontrados")
        print("Revisar y corregir antes del despliegue")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
