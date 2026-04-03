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

results = []

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
            resolves = True
        except Resolver404:
            print(f"    WARNING: No se pudo resolver la URL")
            resolves = False

        # Probar la vista
        if "buscar" in endpoint_name or "search" in endpoint_name:
            test_url = f"{url}?q=test"
        elif "by-code" in endpoint_name:
            test_url = f"{url}?code=TEST123"
        else:
            test_url = url

        response = c.get(test_url)
        status = response.status_code

        # Interpretar los códigos de estado
        status_text = f"Status: {status}"
        if status == 200:
            status_text += " (OK)"
        elif status == 302:
            status_text += " (REDIRECT - probablemente requiere autenticación)"
        elif status == 400:
            status_text += " (BAD REQUEST - posiblemente falta parámetros)"
        elif status == 403:
            status_text += " (FORBIDDEN - requiere permisos)"
        elif status == 404:
            status_text += " (NOT FOUND)"

        print(f"    {status_text}")

        # Guardar resultado
        results.append(
            {
                "endpoint": endpoint_name,
                "url": url,
                "resolves": resolves,
                "status": status,
                "expected_path": expected_path,
            }
        )

    except Exception as e:
        print(f"ERR {endpoint_name:40} -> ERROR: {str(e)}")
        results.append({"endpoint": endpoint_name, "error": str(e), "expected_path": expected_path})

    print("")

print("=== RESUMEN ===")
print("")
print(f"{'Endpoint':40} {'Estado':15} {'Detalles'}")
print("-" * 80)

for result in results:
    endpoint = result["endpoint"]
    if "error" in result:
        print(f"{endpoint:40} {'ERROR':15} {result['error'][:30]}...")
    else:
        status = result["status"]
        if status == 200:
            estado = "OK"
        elif status == 302:
            estado = "REDIRECT"
        elif status == 400:
            estado = "BAD REQUEST"
        elif status == 404:
            estado = "NOT FOUND"
        else:
            estado = f"CODE {status}"

        print(f"{endpoint:40} {estado:15} {result['url']}")

print("\n=== URLs ABSOLUTAS ESPERADAS (Chile) ===")
base_url = "https://www.egarage.cl"
for result in results:
    endpoint_name = result["endpoint"]
    if endpoint_name.startswith("/"):
        # Para URLs directas, usar la ruta esperada
        full_url = f"{base_url}{endpoint_name}"
    else:
        # Para namespaces, construir la URL completa
        if "url" in result:
            full_url = f"{base_url}{result['url']}"
        else:
            full_url = f"{base_url}/{result['expected_path']}"
    print(f"{endpoint_name:40} -> {full_url}")
