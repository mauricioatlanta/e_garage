#!/usr/bin/env python
"""Script para obtener información de STATIC_COUNT, LANGUAGE_CODE y TEMPLATES"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.conf import settings

# STATIC_COUNT
static_root = settings.STATIC_ROOT
if static_root and os.path.exists(static_root):
    file_count = sum(len(files) for _, _, files in os.walk(static_root))
    print(f"STATIC_COUNT: {file_count}")
else:
    print(f"STATIC_COUNT: STATIC_ROOT no existe o no está configurado")
    print(f"STATIC_ROOT: {static_root}")

# LANGUAGE_CODE
print(f"\nLANGUAGE_CODE: {settings.LANGUAGE_CODE}")

# TEMPLATES
print(f"\nTEMPLATES:")
import json
print(json.dumps(settings.TEMPLATES, indent=2, default=str))







