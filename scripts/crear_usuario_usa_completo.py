#!/usr/bin/env python
"""
Script para crear usuario de prueba completo para USA con suscripción activa
Incluye: Usuario, Empresa y Suscripción
"""

import os
import sys
from datetime import datetime, timedelta

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion

User = get_user_model()


def crear_usuario_usa_completo():
    """Crea el usuario de prueba para USA con empresa y suscripción activa"""

    username = "testuser_usa"
    password = "TestUSA2025!"
    email = "testuser@usa-garage.com"

    print("=" * 80)
    print("🇺🇸 CREANDO USUARIO DE PRUEBA PARA USA")
    print("=" * 80)

    # Paso 1: Crear o obtener usuario
    print("\n1️⃣ Creando usuario...")
    try:
        user = User.objects.get(username=username)
        print(f"   ✅ Usuario '{username}' ya existe")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name="Test",
            last_name="USA User",
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        print(f"   ✅ Usuario '{username}' creado exitosamente")

    # Verificar que el usuario está activo
    if not user.is_active:
        user.is_active = True
        user.save()
        print(f"   ✅ Usuario '{username}' activado")

    # Paso 2: Crear o obtener empresa
    print("\n2️⃣ Creando empresa...")
    try:
        empresa = Empresa.objects.get(user=user)
        print(f"   ✅ Empresa '{empresa.nombre_taller}' ya existe")
        # Actualizar país si no es US
        if empresa.pais != "US":
            empresa.pais = "US"
            empresa.save()
            print(f"   ✅ País actualizado a US")
    except Empresa.DoesNotExist:
        empresa = Empresa.objects.create(
            user=user,
            nombre_taller="Taller de testuser_usa",
            empresa="USA Test Garage LLC",
            direccion="123 Main Street, New York, NY 10001",
            telefono="+1-555-123-4567",
            email=email,
            pais="US",  # Importante: país USA
            zona_horaria="America/New_York",
        )
        print(f"   ✅ Empresa '{empresa.nombre_taller}' creada exitosamente")

    # Paso 3: Crear o actualizar suscripción
    print("\n3️⃣ Creando/actualizando suscripción...")
    try:
        suscripcion = Suscripcion.objects.get(user=user)
        print(f"   ✅ Suscripción ya existe (tipo: {suscripcion.tipo})")

        # Actualizar suscripción para asegurar que esté activa y vigente
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=30)  # 30 días de prueba

        suscripcion.tipo = "trial"
        suscripcion.fecha_inicio = fecha_inicio
        suscripcion.fecha_fin = fecha_fin
        suscripcion.activa = True
        suscripcion.save()

        print(f"   ✅ Suscripción actualizada:")
        print(f"      - Tipo: {suscripcion.tipo}")
        print(f"      - Estado: {'Activa' if suscripcion.activa else 'Inactiva'}")
        print(f"      - Fecha inicio: {suscripcion.fecha_inicio}")
        print(f"      - Fecha fin: {suscripcion.fecha_fin}")
        print(f"      - Vigente: {'Sí' if not suscripcion.esta_vencida() else 'No'}")

    except Suscripcion.DoesNotExist:
        # Crear nueva suscripción
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=30)  # 30 días de prueba

        suscripcion = Suscripcion.objects.create(
            user=user,
            tipo="trial",
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activa=True,
        )

        print(f"   ✅ Suscripción creada exitosamente:")
        print(f"      - Tipo: {suscripcion.tipo}")
        print(f"      - Estado: Activa")
        print(f"      - Fecha inicio: {suscripcion.fecha_inicio}")
        print(f"      - Fecha fin: {suscripcion.fecha_fin}")
        print(f"      - Vigente: {'Sí' if not suscripcion.esta_vencida() else 'No'}")

    # Resumen final
    print("\n" + "=" * 80)
    print("✅ USUARIO USA CREADO EXITOSAMENTE")
    print("=" * 80)
    print(f"\n📋 CREDENCIALES DE ACCESO:")
    print(f"   Usuario: {username}")
    print(f"   Contraseña: {password}")
    print(f"   Email: {email}")
    print(f"\n🏢 EMPRESA:")
    print(f"   Nombre: {empresa.nombre_taller}")
    print(f"   País: {empresa.pais}")
    print(f"\n📅 SUSCRIPCIÓN:")
    print(f"   Tipo: {suscripcion.tipo}")
    print(f"   Estado: {'Activa' if suscripcion.activa else 'Inactiva'}")
    print(f"   Vigente: {'Sí' if not suscripcion.esta_vencida() else 'No'}")
    print(f"   Vence: {suscripcion.fecha_fin}")
    print(f"\n🌐 URLs DE ACCESO:")
    print(f"   Login USA: http://127.0.0.1:8000/us/accounts/login/")
    print(f"   Dashboard USA: http://127.0.0.1:8000/us/")
    print("=" * 80)

    return user, empresa, suscripcion


if __name__ == "__main__":
    try:
        crear_usuario_usa_completo()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)



