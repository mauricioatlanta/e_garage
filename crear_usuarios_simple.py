#!/usr/bin/env python3
"""
Script simple para crear usuarios de prueba
"""
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.empresa import Empresa


def crear_usuarios_prueba():
    print("🚀 Creando usuarios de prueba...")

    # Usuario admin
    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@egarage.com",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print("✅ Usuario admin creado")
    else:
        print("ℹ️ Usuario admin ya existe")

    # Usuario taller1
    user1, created = User.objects.get_or_create(
        username="taller1",
        defaults={
            "email": "taller1@egarage.com",
            "first_name": "Carlos",
            "last_name": "Méndez",
            "is_active": True,
        },
    )
    if created:
        user1.set_password("taller123")
        user1.save()
        print("✅ Usuario taller1 creado")
    else:
        # Actualizar password por si acaso
        user1.set_password("taller123")
        user1.save()
        print("ℹ️ Usuario taller1 ya existe - password actualizado")

    # Empresa para taller1
    empresa1, created = Empresa.objects.get_or_create(
        usuario=user1,
        defaults={
            "nombre_taller": "Taller AutoFix",
            "direccion": "Av. Providencia 1234",
            "telefono": "+56912345678",
        },
    )
    if created:
        print("✅ Empresa Taller AutoFix creada")
    else:
        print("ℹ️ Empresa Taller AutoFix ya existe")

    # Usuario taller2
    user2, created = User.objects.get_or_create(
        username="taller2",
        defaults={
            "email": "taller2@egarage.com",
            "first_name": "Ana",
            "last_name": "Rodriguez",
            "is_active": True,
        },
    )
    if created:
        user2.set_password("taller123")
        user2.save()
        print("✅ Usuario taller2 creado")
    else:
        # Actualizar password por si acaso
        user2.set_password("taller123")
        user2.save()
        print("ℹ️ Usuario taller2 ya existe - password actualizado")

    # Empresa para taller2
    empresa2, created = Empresa.objects.get_or_create(
        usuario=user2,
        defaults={
            "nombre_taller": "Taller Premium",
            "direccion": "Av. Las Condes 5678",
            "telefono": "+56987654321",
        },
    )
    if created:
        print("✅ Empresa Taller Premium creada")
    else:
        print("ℹ️ Empresa Taller Premium ya existe")

    print("\n📊 Resumen de cuentas:")
    print(f"   Admin: admin / admin123")
    print(f"   Taller1: taller1 / taller123 ({empresa1.nombre_taller})")
    print(f"   Taller2: taller2 / taller123 ({empresa2.nombre_taller})")

    # Verificar que las passwords funcionan
    print("\n🔍 Verificando autenticación:")
    from django.contrib.auth import authenticate

    auth1 = authenticate(username="taller1", password="taller123")
    if auth1:
        print("✅ taller1 autenticación OK")
    else:
        print("❌ taller1 autenticación FALLA")

    auth2 = authenticate(username="taller2", password="taller123")
    if auth2:
        print("✅ taller2 autenticación OK")
    else:
        print("❌ taller2 autenticación FALLA")


if __name__ == "__main__":
    crear_usuarios_prueba()
