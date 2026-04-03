import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.urls import reverse, resolve, Resolver404
from django.test import Client

c = Client()

# Endpoints del template - CORREGIDOS con namespaces correctos para Chile
# Usamos namespaces específicos de país para Chile
endpoints = [
    ("documentos_cl_es:api_obtener_numero_documento", "documentos/api/obtener-numero-documento"),
    # Ajax endpoints don't have namespace, we'll test them directly
    ("/ajax/clientes/buscar/", "ajax/clientes/buscar"),
    ("/ajax/vehiculos-por-cliente/", "ajax/vehiculos/por-cliente"),
    ("taller:api:repuesto_by_code_api", "api/repuestos/by-code"),
    ("taller:api:buscar_repuestos_api", "api/repuestos/buscar"),
    ("taller:servicios:buscar_servicios_api", "servicios/buscar/api"),
]

print("=== VERIFICACION DE ENDPOINTS (Chile) ===")
print("")

for endpoint_name, expected_path in endpoints:
    try:
        # Si empieza con /, es una URL directa
        if endpoint_name.startswith("/"):
            url = endpoint_name
            print(f"DIR {endpoint_name:40} -> {url}")
        else:
            # Intentar con namespace
            url = reverse(endpoint_name)
            print(f"OK  {endpoint_name:40} -> {url}")

        # Verificar que la URL resuelve
        try:
            match = resolve(url)
            print(f"    Resuelve a: {match.view_name}")
        except Resolver404:
            print(f"    WARNING: No se pudo resolver la URL")

        # Probar la vista
        if "buscar" in endpoint_name or "search" in endpoint_name:
            test_url = f"{url}?q=test"
        elif "by-code" in endpoint_name:
            test_url = f"{url}?code=TEST123"
        else:
            test_url = url

        response = c.get(test_url)
        print(f"    Status: {response.status_code}")

        # Interpretar los códigos de estado
        if response.status_code == 200:
            print(f"    ✅ OK")
        elif response.status_code == 302:
            print(f"    ⚠️  REDIRECT (probablemente requiere autenticación)")
        elif response.status_code == 400:
            print(f"    ⚠️  BAD REQUEST (posiblemente falta parámetros)")
        elif response.status_code == 403:
            print(f"    ⚠️  FORBIDDEN (requiere permisos)")
        elif response.status_code == 404:
            print(f"    ❌ NOT FOUND")
        else:
            print(f"    ⚠️  Código inesperado: {response.status_code}")

    except Exception as e:
        print(f"ERR {endpoint_name:40} -> ERROR: {str(e)}")

    print("")

print("=== URLs ABSOLUTAS ESPERADAS (Chile) ===")
base_url = "https://www.egarage.cl"
for endpoint_name, expected_path in endpoints:
    if endpoint_name.startswith("/"):
        # Para URLs directas, usar la ruta esperada
        full_url = f"{base_url}{endpoint_name}"
    else:
        # Para namespaces, construir la URL completa
        try:
            url_path = reverse(endpoint_name)
            full_url = f"{base_url}{url_path}"
        except:
            full_url = f"{base_url}/{expected_path}"
    print(f"{endpoint_name:40} -> {full_url}")
