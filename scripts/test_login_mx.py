#!/usr/bin/env python
"""
Test: verificar si /mx/es/accounts/login/ usa account/_login_form.html (include con marca EGARAGE_LOGIN_FORM_V1).

Ejecutar desde la raíz del proyecto:
  python manage.py shell < scripts/test_login_mx.py

O desde Django shell:
  from django.test import Client
  r = Client().get("/mx/es/accounts/login/")
  print("EGARAGE_LOGIN_FORM_V1 en HTML:", b"EGARAGE_LOGIN_FORM_V1" in r.content)
  print("r.templates:", getattr(r, "templates", None) or "N/A")
  print("Primeros 500 chars:", r.content[:500])
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.test import Client

client = Client()
r = client.get("/mx/es/accounts/login/")

print("=== Test /mx/es/accounts/login/ ===")
print("EGARAGE_LOGIN_FORM_V1 en HTML:", b"EGARAGE_LOGIN_FORM_V1" in r.content)
print("r.templates:", getattr(r, "templates", None) or "N/A")
print("Status:", r.status_code)
print("--- Primeros 500 chars ---")
print(r.content[:500].decode("utf-8", errors="replace"))
print("---")
