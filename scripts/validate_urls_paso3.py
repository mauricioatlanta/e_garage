#!/usr/bin/env python
"""PASO 3: Validar data-url-service-create y data-url-repuesto-create en el form."""
import re
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
c = Client(HTTP_HOST="www.egarage.cl")

# Autenticar con primer usuario staff/superuser para llegar al form
user = User.objects.filter(is_staff=True).first() or User.objects.first()
if user:
    c.force_login(user)
else:
    print("WARN: No user found, form may redirect to login")

for path in ["/cl/es/documentos/form/", "/us/en/documentos/form/"]:
    r = c.get(path, secure=True, follow=True)
    html = r.content.decode()

    print("\nPATH:", path)
    print("Final status:", r.status_code)

    s = re.search(r'data-url-service-create="([^"]+)"', html)
    p = re.search(r'data-url-repuesto-create="([^"]+)"', html)

    print("SERVICE:", s.group(1) if s else "NOT_FOUND")
    print("PART (repuesto):", p.group(1) if p else "NOT_FOUND")
