#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validación: ui_config.tax_lines por país sin mezcla (IVA solo en CL, Sales Tax solo en US).

Ejecutar desde la raíz del proyecto (PowerShell):
  python -c "exec(open('scripts/validar_tax_por_pais.py', encoding='utf-8').read())"

En bash:
  python manage.py shell < scripts/validar_tax_por_pais.py

Sin usuario logueado las rutas suelen devolver 302 (login); entonces la validación
de HTML se salta. Para comprobar la lógica de contexto sin HTTP, usar:
  pytest taller/tests/test_country_features.py -v
(incluye test_us_replaces_previous_tax_lines_no_mixing y test_cl_replaces_previous_tax_lines_no_mixing.)

Comprueba que el HTML renderizado para /us/... no contenga IVA y sí Sales Tax,
y que /cl/... no contenga Sales Tax y sí IVA. HTTP_HOST en una sola línea para
evitar errores de copy/paste.
"""
import os
import sys
import re

# Asegurar Django
if "django" not in sys.modules:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
    import django

    django.setup()

from django.test import Client


def main():
    client = Client()
    host = "www.egarage.cl"

    # Usuario anónimo: la vista puede redirigir a login; aun así el contexto
    # se construye antes del redirect en algunas rutas. Probamos la función
    # de contexto directamente en tests; aquí validamos el render si hay 200.
    paths = [
        ("/us/documentos/form/", "US", "Sales Tax", "IVA"),
        ("/cl/documentos/form/", "CL", "IVA", "Sales Tax"),
    ]
    ok = 0
    for path, country, must_contain, must_not_contain in paths:
        resp = client.get(path, HTTP_HOST=host)
        html = resp.content.decode("utf-8", errors="replace") if resp.content else ""

        has_expected = must_contain in html
        has_forbidden = must_not_contain in html

        if resp.status_code == 200:
            if has_expected and not has_forbidden:
                print(
                    f"OK {country} {path}: contiene '{must_contain}', no contiene '{must_not_contain}'"
                )
                ok += 1
            else:
                print(
                    f"FAIL {country} {path}: expected '{must_contain}' in HTML, forbidden '{must_not_contain}'"
                )
                print(
                    f"  status={resp.status_code} has_expected={has_expected} has_forbidden={has_forbidden}"
                )
        else:
            # Redirect a login u otro: igualmente comprobar que no haya mezcla en el body
            if has_forbidden:
                print(
                    f"WARN {country} {path}: status {resp.status_code} pero HTML contiene '{must_not_contain}'"
                )
            else:
                print(f"SKIP {country} {path}: status {resp.status_code} (login?)")

    # JSON uiConfigTaxLines si existe en la respuesta
    if paths:
        resp = client.get("/us/documentos/form/", HTTP_HOST=host)
        html = resp.content.decode("utf-8", errors="replace") if resp.content else ""
        m = re.search(r'<script id="uiConfigTaxLines"[^>]*>([^<]+)</script>', html)
        if m:
            import json

            try:
                data = json.loads(m.group(1).strip())
                lines = data if isinstance(data, list) else data.get("tax_lines", [])
                labels = [x.get("label", "") for x in lines]
                if len(labels) == 1 and labels[0] == "Sales Tax":
                    print("OK uiConfigTaxLines (US): una sola línea Sales Tax")
                    ok += 1
                else:
                    print("FAIL uiConfigTaxLines (US): expected single Sales Tax, got", labels)
            except Exception as e:
                print("WARN uiConfigTaxLines parse error:", e)
        else:
            print("SKIP uiConfigTaxLines no encontrado (puede ser página de login)")

    print("Validación terminada.")
    return 0 if ok >= 2 else 1


if __name__ == "__main__":
    sys.exit(main())
