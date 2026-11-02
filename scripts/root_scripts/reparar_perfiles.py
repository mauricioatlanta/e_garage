#!/usr/bin/env python3
"""
Reparación de perfiles de usuario faltantes
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from django.contrib.auth.models import User

from taller.models.empresa import Empresa
from taller.models.perfil_usuario import PerfilUsuario

print("🔧 === REPARACIÓN PERFILES ===")

# Usuarios que necesitan perfiles
usuarios_a_reparar = ["taller1", "test_totales", "test_campos", "test_mecanicos"]

for username in usuarios_a_reparar:
    try:
        user = User.objects.get(username=username)

        # Verificar si ya tiene perfil
        try:
            perfil = PerfilUsuario.objects.get(user=user)
            print(f"✅ {username} ya tiene perfil")
            continue
        except PerfilUsuario.DoesNotExist:
            pass

        # Buscar empresa asociada
        try:
            empresa = Empresa.objects.get(usuario=user)
            print(f"📍 Empresa encontrada para {username}: {empresa.nombre_taller}")

            # Crear perfil
            perfil = PerfilUsuario.objects.create(user=user, empresa=empresa, rol="admin")
            print(f"✅ Perfil creado para {username}")

        except Empresa.DoesNotExist:
            print(f"❌ {username} no tiene empresa asociada")

    except User.DoesNotExist:
        print(f"❌ Usuario {username} no existe")

print()
print("👥 === ESTADO FINAL PERFILES ===")
perfiles = PerfilUsuario.objects.all()
for perfil in perfiles:
    print(f"  - {perfil.user.username}: {perfil.empresa.nombre_taller} ({perfil.rol})")

print()
print("🏁 === REPARACIÓN COMPLETADA ===")
