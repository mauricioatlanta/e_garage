#!/usr/bin/env python
"""
Checklist de Pre-Despliegue a Produccion para eGarage Django
Version simplificada sin emojis
"""

import os
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


def check_security_settings():
    """Verificar configuraciones de seguridad"""
    print("VERIFICANDO CONFIGURACIONES DE SEGURIDAD")
    print("=" * 50)

    issues = []

    # DEBUG
    if settings.DEBUG:
        issues.append("ERROR: DEBUG=True (debe ser False en produccion)")
    else:
        print("OK: DEBUG=False")

    # ALLOWED_HOSTS
    if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ["*"]:
        issues.append("ERROR: ALLOWED_HOSTS no configurado correctamente")
    else:
        print(f"OK: ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

    # SECRET_KEY
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here":
        issues.append("ERROR: SECRET_KEY no configurado")
    else:
        print("OK: SECRET_KEY configurado")

    if issues:
        print("\nPROBLEMAS DE SEGURIDAD ENCONTRADOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\nTODAS LAS CONFIGURACIONES DE SEGURIDAD OK")

    return len(issues) == 0


def check_static_files():
    """Verificar archivos estaticos"""
    print("\nVERIFICANDO ARCHIVOS ESTATICOS")
    print("=" * 50)

    issues = []

    # WhiteNoise
    if hasattr(settings, "STATICFILES_STORAGE"):
        if "whitenoise" in settings.STATICFILES_STORAGE:
            print("OK: WhiteNoise configurado")
        else:
            issues.append("WARNING: WhiteNoise no configurado")
    else:
        issues.append("ERROR: STATICFILES_STORAGE no configurado")

    # STATIC_ROOT
    if hasattr(settings, "STATIC_ROOT") and settings.STATIC_ROOT:
        print(f"OK: STATIC_ROOT: {settings.STATIC_ROOT}")
    else:
        issues.append("ERROR: STATIC_ROOT no configurado")

    # Verificar archivos criticos
    critical_files = [
        "static/taller/common/js/documentos_form.js",
    ]

    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"OK: {file_path} existe")
        else:
            issues.append(f"ERROR: {file_path} no encontrado")

    if issues:
        print("\nPROBLEMAS CON ARCHIVOS ESTATICOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\nARCHIVOS ESTATICOS OK")

    return len(issues) == 0


def check_database():
    """Verificar base de datos"""
    print("\nVERIFICANDO BASE DE DATOS")
    print("=" * 50)

    issues = []

    try:
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("OK: Conexion a base de datos OK")
    except Exception as e:
        issues.append(f"ERROR: Error de conexion DB: {e}")

    # Verificar modelos criticos
    try:
        from taller.models import Cliente, Documento, Empresa, Vehiculo

        doc_count = Documento.objects.count()
        emp_count = Empresa.objects.count()
        cli_count = Cliente.objects.count()
        veh_count = Vehiculo.objects.count()

        print(f"OK: Documentos: {doc_count}")
        print(f"OK: Empresas: {emp_count}")
        print(f"OK: Clientes: {cli_count}")
        print(f"OK: Vehiculos: {veh_count}")

    except Exception as e:
        issues.append(f"ERROR: Error accediendo a modelos: {e}")

    if issues:
        print("\nPROBLEMAS CON BASE DE DATOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\nBASE DE DATOS OK")

    return len(issues) == 0


def smoke_test():
    """Smoke test funcional"""
    print("\nSMOKE TEST FUNCIONAL")
    print("=" * 50)

    issues = []
    client = Client()

    # Test Chile
    print("\nTesting Chile (CLP + IVA 19%)")
    try:
        login_success = client.login(username="test_chile", password="test123")
        if login_success:
            print("OK: Login CL exitoso")
            response = client.get("/cl/es/documentos/form/")
            if response.status_code == 200:
                print("OK: Formulario CL carga correctamente")
            else:
                issues.append(f"ERROR: Formulario CL error: {response.status_code}")
        else:
            issues.append("ERROR: Login CL fallo")
    except Exception as e:
        issues.append(f"ERROR: Error en test CL: {e}")

    # Test USA
    print("\nTesting USA (USD + Sales Tax 0%)")
    try:
        login_success = client.login(username="testuser_usa", password="TestUSA2025!")
        if login_success:
            print("OK: Login US exitoso")
            response = client.get("/us/en/documentos/form/")
            if response.status_code == 200:
                print("OK: Formulario US carga correctamente")
            else:
                issues.append(f"ERROR: Formulario US error: {response.status_code}")
        else:
            issues.append("ERROR: Login US fallo")
    except Exception as e:
        issues.append(f"ERROR: Error en test US: {e}")

    # Test JavaScript
    print("\nTesting JavaScript")
    try:
        response = client.get("/static/taller/common/js/documentos_form.js")
        if response.status_code == 200:
            print("OK: JavaScript carga correctamente")
            content = response.content.decode("utf-8")
            if "recalcTotals" in content:
                print("OK: Funcion recalcTotals encontrada")
            if "VAT_PCT" in content:
                print("OK: Variable VAT_PCT encontrada")
        else:
            issues.append(f"ERROR: JavaScript error: {response.status_code}")
    except Exception as e:
        issues.append(f"ERROR: Error en test JS: {e}")

    if issues:
        print("\nPROBLEMAS EN SMOKE TEST:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\nSMOKE TEST OK")

    return len(issues) == 0


def main():
    """Ejecutar checklist completo"""
    print("CHECKLIST DE PRE-DESPLIEGUE A PRODUCCION")
    print("=" * 60)
    print("eGarage Django - Verificacion completa")
    print("=" * 60)

    results = []

    # Ejecutar verificaciones
    results.append(("Seguridad", check_security_settings()))
    results.append(("Archivos Estaticos", check_static_files()))
    results.append(("Base de Datos", check_database()))
    results.append(("Smoke Test", smoke_test()))

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
        print("\nSISTEMA LISTO PARA PRODUCCION!")
        print("Todas las verificaciones pasaron")
    else:
        print(f"\n{total - passed} problemas encontrados")
        print("Revisar y corregir antes del despliegue")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
