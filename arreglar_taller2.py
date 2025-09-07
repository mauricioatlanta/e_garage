#!/usr/bin/env python3
"""
Script para diagnosticar y arreglar el usuario taller2
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from taller.models.empresa import Empresa

print("🔍 DIAGNÓSTICO USUARIO TALLER2")
print("=" * 50)

try:
    user = User.objects.get(username="taller2")
    print(f"✅ Usuario taller2 encontrado:")
    print(f"   Email: {user.email}")
    print(f"   Activo: {user.is_active}")
    print(f"   Staff: {user.is_staff}")
    print(f"   Superuser: {user.is_superuser}")
    print(f"   Fecha creación: {user.date_joined}")
    print(f"   Último login: {user.last_login}")

    # Verificar autenticación
    auth_result = authenticate(username="taller2", password="taller123")
    print(f'   Autenticación con "taller123": {"✅ OK" if auth_result else "❌ FALLO"}')

    # Verificar password manualmente
    is_correct = user.check_password("taller123")
    print(f'   Password check directo: {"✅ OK" if is_correct else "❌ FALLO"}')

    # Verificar empresa asociada
    try:
        empresa = Empresa.objects.get(usuario=user)
        print(f"   Empresa asociada: {empresa.nombre_taller}")
    except Empresa.DoesNotExist:
        print(f"   ❌ Sin empresa asociada")

    # Si el password está mal, lo arreglamos
    if not is_correct:
        print("\n🔧 ARREGLANDO PASSWORD...")
        user.set_password("taller123")
        user.save()
        print('✅ Password actualizado a "taller123"')

        # Verificar nuevamente
        auth_result = authenticate(username="taller2", password="taller123")
        print(f'   Verificación post-arreglo: {"✅ OK" if auth_result else "❌ FALLO"}')

except User.DoesNotExist:
    print("❌ Usuario taller2 no existe, creando...")

    # Crear usuario taller2
    user = User.objects.create_user(
        username="taller2",
        email="taller2@test.com",
        password="taller123",
        first_name="Ana",
        last_name="Rodriguez",
        is_active=True,
    )
    print("✅ Usuario taller2 creado")

    # Crear empresa asociada
    empresa, created = Empresa.objects.get_or_create(
        usuario=user,
        defaults={
            "nombre_taller": "Mecánica Express",
            "direccion": "Av. Las Condes 5678",
            "telefono": "+56987654321",
        },
    )
    if created:
        print("✅ Empresa asociada creada")
    else:
        print("ℹ️ Empresa ya existía")

print("\n🧪 PRUEBA FINAL DE AUTENTICACIÓN:")
auth_result = authenticate(username="taller2", password="taller123")
if auth_result:
    print("✅ taller2 puede autenticarse correctamente")
    print("🎯 Credenciales: taller2 / taller123")
else:
    print("❌ Aún hay problemas con la autenticación")

print("\n" + "=" * 50)
print("🔑 CREDENCIALES ACTUALIZADAS:")
print("   👑 Admin: admin / admin123")
print("   🔧 Taller 1: taller1 / taller123")
print("   🔧 Taller 2: taller2 / taller123")
print("=" * 50)
