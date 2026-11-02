#!/usr/bin/env python
# Diagnóstico formulario documentos: id_apply_vat, tax-checkbox, t_total, uiConfigTaxLines.
# Servidor: cd /srv/egarage && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod
# Luego: python manage.py shell < scripts/diagnose_document_form_tax.py
# O pegar en el shell (sin saltos de línea dentro de strings) el bloque que está abajo en COPIAR_PEGAR.

from django.test import Client
from django.contrib.auth import get_user_model
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")

U = get_user_model()
u = U.objects.filter(username="justenvios").first() or U.objects.first()
if not u:
    print("ERROR: No user found (justenvios or first)")
    sys.exit(1)

c = Client(HTTP_HOST="www.egarage.cl")
c.force_login(u)
r = c.get("/us/documentos/form/?cliente_id=4&vehiculo_id=13", secure=True)
h = r.content.decode("utf-8", "ignore")

print("STATUS:", r.status_code)
print("HAS id_apply_vat:", 'id="id_apply_vat"' in h)
print("HAS tax-checkbox:", "tax-checkbox" in h)
print("HAS t_total:", 'id="t_total"' in h)

i = h.find("uiConfigTaxLines")
print("\nSCRIPT SNIPPET:")
if i != -1:
    print(h[max(0, i - 200) : i + 400])
else:
    print("NO SCRIPT FOUND")
