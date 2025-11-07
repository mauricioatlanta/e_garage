from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== SMOKE TEST MULTI-TENANT ===")

client = Client()

# Test Chile
print("\n1. Testing Chile (CLP + IVA 19%)")
try:
    login_success = client.login(username='admin_chile', password='admin123')
    if login_success:
        print("✅ Login CL exitoso")
        response = client.get('/cl/es/documentos/form/')
        print(f"📄 Form CL: {response.status_code}")
        if response.status_code == 200:
            print("✅ Formulario CL cargado")
        else:
            print("❌ Error en formulario CL")
    else:
        print("❌ Login CL falló")
except Exception as e:
    print(f"❌ Error CL: {e}")

# Test USA
print("\n2. Testing USA (USD + Sales Tax 0%)")
try:
    login_success = client.login(username='testuser_usa', password='TestUSA2025!')
    if login_success:
        print("✅ Login US exitoso")
        response = client.get('/us/en/documentos/form/')
        print(f"📄 Form US: {response.status_code}")
        if response.status_code == 200:
            print("✅ Formulario US cargado")
        else:
            print("❌ Error en formulario US")
    else:
        print("❌ Login US falló")
except Exception as e:
    print(f"❌ Error US: {e}")

# Test JavaScript
print("\n3. Testing JavaScript")
try:
    response = client.get('/static/taller/common/js/documentos_form.js')
    if response.status_code == 200:
        print("✅ JavaScript cargado")
        content = response.content.decode('utf-8')
        if 'recalcTotals' in content:
            print("✅ Función recalcTotals encontrada")
        if 'VAT_PCT' in content:
            print("✅ Variable VAT_PCT encontrada")
    else:
        print("❌ JavaScript no cargado")
except Exception as e:
    print(f"❌ Error JS: {e}")

print("\n=== SMOKE TEST COMPLETADO ===")
