#!/usr/bin/env python
"""
Test signup flow - verifica que registro exitoso incluye link correcto a bienvenida.

IMPORTANTE: HTTP_HOST debe ser un dominio válido, sin markdown.
  ❌ Client(HTTP_HOST="[www.egarage.cl](http://www.egarage.cl)")  # markdown pegado
  ✅ Client(HTTP_HOST="www.egarage.cl")                            # correcto
"""
import os
import sys
import uuid

# Asegurar que Django esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

import django

django.setup()

from django.test import Client


def main():
    c = Client(headers={"host": "www.egarage.cl"})
    email = "ok_" + uuid.uuid4().hex[:6] + "@test.com"

    r = c.post(
        "/accounts/signup/?from=cl",
        data={
            "email": email,
            "username": email,
            "password1": "Test123456!!",
            "password2": "Test123456!!",
            "country": "CL",
            "nombre_taller": "OKTest",
            "telefono": "+56912345678",
        },
        secure=True,
        follow=True,
    )

    html = r.content.decode("utf-8", "ignore")

    print("STATUS=", r.status_code)
    print("HAS_BIENVENIDA_LINK=", "/cl/es/bienvenida/" in html)
    print(
        "HAS_TEMPLATE=",
        any("registro_exitoso" in str(getattr(t, "name", "")) for t in getattr(r, "templates", [])),
    )
    print()
    print("--- Primeros 800 chars del HTML ---")
    print(html[:800])

    if r.status_code == 200 and "/cl/es/bienvenida/" in html:
        print("\n[OK] Test OK: signup genera link correcto a /cl/es/bienvenida/")
    else:
        print("\n[FAIL] Test fallo: revisar STATUS y HAS_BIENVENIDA_LINK")
        sys.exit(1)


if __name__ == "__main__":
    main()
