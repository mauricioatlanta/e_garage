#!/usr/bin/env python3
"""
Script para verificar usuarios y credenciales de prueba
"""

import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from taller.models.empresa import Empresa

demo_definiciones = [
    {
        "username": "demo_cl",
        "password": "Chile123!",
        "descripcion": "🇨🇱 Taller demo Chile",
        "pais": "CL",
        "email": "demo_cl@egarage.mx",
        "nombre_taller": "Demo Taller Chile",
        "moneda": "CLP",
        "zona_horaria": "America/Santiago",
    },
    {
        "username": "demo_us",
        "password": "Usa12345!",
        "descripcion": "🇺🇸 Workshop demo USA",
        "pais": "US",
        "email": "demo_us@egarage.mx",
        "nombre_taller": "Demo Workshop USA",
        "moneda": "USD",
        "zona_horaria": "America/New_York",
    },
    {
        "username": "demo_br",
        "password": "Brasil123!",
        "descripcion": "🇧🇷 Oficina demo Brasil",
        "pais": "BR",
        "email": "demo_br@egarage.mx",
        "nombre_taller": "Demo Oficina Brasil",
        "moneda": "BRL",
        "zona_horaria": "America/Sao_Paulo",
    },
    {
        "username": "demo_pe",
        "password": "Peru123!",
        "descripcion": "🇵🇪 Taller demo Perú",
        "pais": "PE",
        "email": "demo_pe@egarage.mx",
        "nombre_taller": "Demo Taller Perú",
        "moneda": "PEN",
        "zona_horaria": "America/Lima",
    },
    {
        "username": "demo_ve",
        "password": "Venezuela123!",
        "descripcion": "🇻🇪 Taller demo Venezuela",
        "pais": "VE",
        "email": "demo_ve@egarage.mx",
        "nombre_taller": "Demo Taller Venezuela",
        "moneda": "VES",
        "zona_horaria": "America/Caracas",
    },
    {
        "username": "demo_mx",
        "password": "Mexico123!",
        "descripcion": "🇲🇽 Taller demo México",
        "pais": "MX",
        "email": "demo_mx@egarage.mx",
        "nombre_taller": "Demo Taller México",
        "moneda": "MXN",
        "zona_horaria": "America/Mexico_City",
    },
]


def asegurar_credenciales_demo():
    print("=" * 80)
    print("🔐 USUARIOS DEMO POR PAÍS")
    print("=" * 80)
    print()

    for cred in demo_definiciones:
        user, created = User.objects.get_or_create(
            username=cred["username"],
            defaults={
                "email": cred["email"],
                "first_name": cred["nombre_taller"].split()[0],
                "last_name": cred["nombre_taller"].split()[-1],
                "is_staff": False,
                "is_superuser": False,
            },
        )

        if created:
            user.set_password(cred["password"])
            user.save()
            estado_user = "🆕 Creado"
        else:
            # Aseguramos contraseña actualizada para consistencia demo
            user.set_password(cred["password"])
            user.email = cred["email"]
            user.save()
            estado_user = "♻️ Actualizado"

        empresa, empresa_creada = Empresa.objects.get_or_create(
            user=user,
            defaults={
                "nombre_taller": cred["nombre_taller"],
                "pais": cred["pais"],
                "moneda": cred["moneda"],
                "zona_horaria": cred["zona_horaria"],
                "plan": "premium",
            },
        )

        if not empresa_creada:
            empresa.nombre_taller = cred["nombre_taller"]
            empresa.pais = cred["pais"]
            empresa.moneda = cred["moneda"]
            empresa.zona_horaria = cred["zona_horaria"]
            empresa.plan = empresa.plan or "premium"
            empresa.save()
            estado_empresa = "🔁 Empresa actualizada"
        else:
            estado_empresa = "🏭 Empresa creada"

        print(
            f"{cred['username']:<12} | {cred['password']:<15} | {cred['descripcion']:<35} | {estado_user} / {estado_empresa}"
        )


def mostrar_credenciales_globales():
    print()
    print("📋 CREDENCIALES PRINCIPALES (legacy):")
    print("-" * 60)

    usuarios_prueba = [
        ("admin", "admin123", "👑 Administrador del sistema"),
        ("taller1", "taller123", "🔧 Taller AutoFix"),
        ("taller2", "taller123", "🔧 Taller Premium"),
    ]

    for username, password, descripcion in usuarios_prueba:
        user = authenticate(username=username, password=password)
        estado = "✅ VÁLIDO" if user else "❌ INVÁLIDO"
        print(f"{username:<12} | {password:<12} | {estado} | {descripcion}")


asegurar_credenciales_demo()
mostrar_credenciales_globales()

print()
print("🗂️ TODOS LOS USUARIOS EN BASE DE DATOS:")
print("-" * 70)

for user in User.objects.all():
    # Buscar empresa asociada
    try:
        empresa = Empresa.objects.get(user=user)
        empresa_info = f"({empresa.nombre_taller} – {empresa.pais})"
    except Empresa.DoesNotExist:
        empresa_info = "(Sin empresa)"

    # Buscar suscripción
    try:
        suscripcion = user.suscripcion
        suscripcion_info = f"{suscripcion.plan} - {'Activa' if suscripcion.activa else 'Inactiva'}"
    except:
        suscripcion_info = "Sin suscripción"

    estado_user = (
        "👑 Admin" if user.is_superuser else ("👤 Staff" if user.is_staff else "👥 Usuario")
    )

    print(f"{user.username:<15} | {user.email:<25} | {estado_user} | {empresa_info}")
    if hasattr(user, "suscripcion"):
        print(f'{"" : <15} | {"" : <25} | 📅 {suscripcion_info}')

print()
print("🎯 ACCESO RÁPIDO:")
print("-" * 30)
print("🌐 URL: http://127.0.0.1:8000/")
print("📊 Admin: http://127.0.0.1:8000/admin/")
print("📈 Reportes: http://127.0.0.1:8000/reportes/")
print()
print("🔑 CREDENCIALES DE ACCESO:")
print("   👑 Admin: admin / admin123")
print("   🔧 Taller 1: taller1 / taller123")
print("   🔧 Taller 2: taller2 / taller123")
print()
print("=" * 80)
