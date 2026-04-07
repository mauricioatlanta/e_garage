from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
import re

U = get_user_model()
u = U.objects.filter(is_superuser=True).first() or U.objects.first()

rf = RequestFactory()
req = rf.get("/cl/es/documentos/form/")
req.user = u

html = render_to_string(
    "taller/common/documentos/document_form.html",
    {"country_code": "cl", "lang_code": "es"},
    request=req,
)

print("=== CHECK ENDPOINT IN TEMPLATE ===")
m = re.search(r'data-url-service-search="([^"]+)"', html)
print("SERVICE_SEARCH_URL =", m.group(1) if m else "NOT FOUND")

print("\n=== CHECK BUTTON & CONTAINER ===")
print("HAS add-servicio =", 'id="add-servicio"' in html)
print("HAS servicios-container =", 'id="servicios-container"' in html)

c = Client()
r = c.get("/cl/es/documentos/form/")
print("\n=== FORM HTTP ===")
print("FORM_STATUS =", r.status_code)

url = m.group(1) if m else "/cl/es/api/servicios/buscar/"
r2 = c.get(url + "?q=aceite")
print("\n=== API HTTP ===")
print("API_URL =", url)
print("API_STATUS =", r2.status_code)
print("API_CT =", r2.get("Content-Type"))
print("API_BODY =", r2.content[:300])
