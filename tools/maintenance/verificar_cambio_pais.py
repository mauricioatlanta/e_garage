#!/usr/bin/env python
"""
Script de verificación del cambio de país
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models import Empresa

try:
    user = User.objects.get(username="testuser_usa")
    empresa = Empresa.objects.get(user=user)
    print(f"Usuario: {user.username}")
    print(f"Empresa: {empresa.nombre_taller}")
    print(f"País: {empresa.pais}")
    print(
        f"Status: {'✅ Correcto (US)' if empresa.pais == 'US' else '❌ Incorrecto (debe ser US)'}"
    )
except Exception as e:
    print(f"Error: {e}")
