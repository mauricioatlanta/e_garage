#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.empresa import Empresa

print("🔍 USUARIOS EXISTENTES EN EL SISTEMA:")
print("=" * 50)

for user in User.objects.all()[:10]:
    try:
        empresa = Empresa.objects.get(user=user)
        print(f"✅ Usuario: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Empresa: {empresa.nombre_taller}")
        print(f"   País: {empresa.get_pais_display()}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Superuser: {user.is_superuser}")
        print()
    except Empresa.DoesNotExist:
        print(f"❌ Usuario: {user.username} - Sin empresa asociada")
        print()

print("🔐 CREDENCIALES PARA PROBAR:")
print("- Usuario: mauricio / Password: [password del usuario]")
print("- Usuario: admin / Password: admin123")
print("- Usuario: mauricio1 / Password: taller123")
print()
print("🌐 URLs DE ACCESO:")
print("- Login: http://127.0.0.1:8000/accounts/login/")
print("- Dashboard: http://127.0.0.1:8000/taller/dashboard/")
print("- Centro Operaciones: http://127.0.0.1:8000/taller/centro-operaciones/")
