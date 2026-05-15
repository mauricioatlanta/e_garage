import os
import sys
import django
import re

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.test import Client

c = Client(HTTP_HOST="www.egarage.cl")
r = c.get("/cl/documentos/form/", secure=True)
s = r.content.decode("utf-8", "ignore")

pats = [
    "data-url-next-number",
    "data-url-client-search",
    "data-url-vehiculos-by-cli",
    "data-url-repuesto-by-code",
    "data-url-repuesto-search",
    "data-url-service-search",
]

print("=== ENDPOINTS EN HTML (data-attributes) ===")
for p in pats:
    m = re.search(r"%s=\"([^\"]+)\"" % p, s)
    print(f"{p:30} => {m.group(1) if m else 'MISSING'}")

# También buscar URLs en scripts
print("\n=== URLs EN SCRIPTS JS ===")
script_urls = [
    "URL_NEXT_NUMBER",
    "URL_CLIENT_SEARCH",
    "URL_VEHICULOS_BY_CLI",
    "URL_REPUESTO_BY_CODE",
    "URL_REPUESTO_SEARCH",
    "URL_SERVICE_SEARCH",
]

for url_var in script_urls:
    pattern = r'%s\s*[:=]\s*[\'"]([^\'"]+)[\'"]' % url_var
    m = re.search(pattern, s)
    if m:
        print(f"{url_var:30} => {m.group(1)}")

# Buscar URLs absolutas
print("\n=== URLs ABSOLUTAS ENCONTRADAS ===")
absolute_urls = re.findall(r'(https?://[^\s\'"]+)', s)
for url in absolute_urls[:10]:  # Mostrar solo las primeras 10
    if any(x in url for x in ["repuesto", "servicio", "cliente", "vehiculo", "documento"]):
        print(url)
