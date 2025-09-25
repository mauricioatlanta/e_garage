#!/usr/bin/env python
"""Script simple para cambiar contraseña"""

import os
import sys

sys.path.append(".")
os.environ["DJANGO_SETTINGS_MODULE"] = "gestion_taller.settings"

import django

django.setup()

from django.contrib.auth.models import User

# Cambiar contraseña del usuario test_diagnostic
user = User.objects.get(username="test_diagnostic")
user.set_password("test123")
user.save()

print(f"Contraseña cambiada para {user.username}")
print("Nueva contraseña: test123")
print("Ahora puedes iniciar sesión y acceder al documento 45")
