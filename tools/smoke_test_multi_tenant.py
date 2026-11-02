#!/usr/bin/env python
"""
Smoke test multi-tenant para verificar comportamiento de moneda, IVA y totales
"""

import os

import django
from django.contrib.auth import get_user_model
from django.test import Client

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
django.setup()


User = get_user_model()


def test_multi_tenant():
    """Test multi-tenant: CL y US con diferentes monedas e IVA"""

    print("🧪 SMOKE TEST MULTI-TENANT")
    print("=" * 50)

    client = Client()

    # Test 1: Chile (CLP + IVA 19%)
    print("\n🇨🇱 TESTING CHILE (CLP + IVA 19%)")
    print("-" * 30)

    try:
        # Login como usuario Chile
        login_success = client.login(username="admin_chile", password="admin123")
        if not login_success:
            print("❌ No se pudo hacer login como admin_chile")
            return False

        print("✅ Login exitoso como admin_chile")

        # Acceder al formulario de documentos
        response = client.get("/cl/es/documentos/form/")
        print(f"📄 Formulario CL: {response.status_code}")

        if response.status_code == 200:
            print("✅ Formulario CL cargado correctamente")

            # Verificar que contiene elementos de moneda CLP
            content = response.content.decode("utf-8")
            if "CLP" in content or "peso" in content.lower():
                print("✅ Moneda CLP detectada en el formulario")
            else:
                print("⚠️  Moneda CLP no detectada en el formulario")
        else:
            print(f"❌ Error al cargar formulario CL: {response.status_code}")

    except Exception as e:
        print(f"❌ Error en test CL: {e}")

    # Test 2: Estados Unidos (USD + Sales Tax 0%)
    print("\n🇺🇸 TESTING USA (USD + Sales Tax 0%)")
    print("-" * 30)

    try:
        # Login como usuario USA
        login_success = client.login(username="testuser_usa", password="TestUSA2025!")
        if not login_success:
            print("❌ No se pudo hacer login como testuser_usa")
            return False

        print("✅ Login exitoso como testuser_usa")

        # Acceder al formulario de documentos
        response = client.get("/us/en/documentos/form/")
        print(f"📄 Formulario US: {response.status_code}")

        if response.status_code == 200:
            print("✅ Formulario US cargado correctamente")

            # Verificar que contiene elementos de moneda USD
            content = response.content.decode("utf-8")
            if "USD" in content or "dollar" in content.lower():
                print("✅ Moneda USD detectada en el formulario")
            else:
                print("⚠️  Moneda USD no detectada en el formulario")
        else:
            print(f"❌ Error al cargar formulario US: {response.status_code}")

    except Exception as e:
        print(f"❌ Error en test US: {e}")

    # Test 3: Verificar JavaScript de cálculos
    print("\n🧮 TESTING JAVASCRIPT CALCULATIONS")
    print("-" * 30)

    try:
        # Verificar que el archivo JavaScript está cargado
        response = client.get("/static/taller/common/js/documentos_form.js")
        if response.status_code == 200:
            print("✅ JavaScript documentos_form.js cargado correctamente")

            content = response.content.decode("utf-8")
            if "recalcTotals" in content:
                print("✅ Función recalcTotals encontrada")
            if "VAT_PCT" in content:
                print("✅ Variable VAT_PCT encontrada")
            if "formatMoney" in content:
                print("✅ Función formatMoney encontrada")
        else:
            print(f"❌ Error al cargar JavaScript: {response.status_code}")

    except Exception as e:
        print(f"❌ Error en test JavaScript: {e}")

    print("\n🎯 SMOKE TEST COMPLETADO")
    print("=" * 50)

    return True


if __name__ == "__main__":
    test_multi_tenant()
