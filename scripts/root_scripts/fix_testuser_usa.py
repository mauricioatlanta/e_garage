#!/usr/bin/env python
"""
Script para verificar y corregir las credenciales de testuser_usa
"""
import os
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from taller.models import Empresa, Suscripcion

User = get_user_model()


def verificar_y_corregir_testuser_usa():
    """Verifica y corrige las credenciales de testuser_usa"""

    print("=" * 70)
    print("🔍 VERIFICACIÓN Y CORRECCIÓN DE testuser_usa")
    print("=" * 70)
    print()

    username = "testuser_usa"
    password = "TestUSA2025!"
    email = "testuser@usa-garage.com"

    # 1. Verificar si el usuario existe
    try:
        user = User.objects.get(username=username)
        print(f"✅ Usuario '{username}' encontrado")
        print(f"   Email: {user.email}")
        print(f"   Activo: {user.is_active}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Superuser: {user.is_superuser}")
        print()
    except User.DoesNotExist:
        print(f"❌ Usuario '{username}' NO existe. Creando usuario...")
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name="Test",
                last_name="User USA",
                is_active=True,
            )
            print(f"✅ Usuario '{username}' creado exitosamente")
            print()

    # 2. Resetear contraseña para asegurar que funcione
    print("🔑 Reseteando contraseña...")
    user.set_password(password)
    user.save()
    print(f"✅ Contraseña reseteada a: {password}")
    print()

    # 3. Asegurar que el usuario esté activo
    if not user.is_active:
        user.is_active = True
        user.save()
        print("✅ Usuario activado")
        print()

    # 4. Verificar/Crear empresa
    try:
        empresa = user.empresa
        print(f"✅ Empresa encontrada: {empresa.nombre_taller}")
        print(f"   País: {empresa.pais}")
        print(f"   Moneda: {empresa.moneda or 'USD'}")

        # Asegurar que el país sea US
        if empresa.pais != "US":
            empresa.pais = "US"
            empresa.save()
            print(f"✅ País de empresa actualizado a US")
        print()
    except AttributeError:
        print("❌ Usuario no tiene empresa asociada. Creando empresa...")
        with transaction.atomic():
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller="Taller de testuser_usa",
                pais="US",
                telefono="+15551234567",
                direccion="Miami, FL, USA",
                moneda="USD",
            )
            print(f"✅ Empresa creada: {empresa.nombre_taller}")
            print(f"   País: {empresa.pais}")
            print(f"   Moneda: {empresa.moneda}")
            print()

    # 5. Verificar/Crear suscripción
    try:
        suscripcion = user.suscripcion
        print(f"✅ Suscripción encontrada:")
        print(f"   Tipo: {suscripcion.tipo}")
        print(f"   Activa: {suscripcion.activa}")
        print(f"   Fecha inicio: {suscripcion.fecha_inicio}")
        print(f"   Fecha fin: {suscripcion.fecha_fin}")

        # Verificar si está vencida
        if hasattr(suscripcion, "esta_vencida"):
            vencida = suscripcion.esta_vencida()
            print(f"   Vencida: {vencida}")

        # Si está vencida o inactiva, crear nueva suscripción trial
        if not suscripcion.activa or (
            hasattr(suscripcion, "esta_vencida") and suscripcion.esta_vencida()
        ):
            print("⚠️ Suscripción vencida o inactiva. Creando nueva suscripción trial...")
            with transaction.atomic():
                # Desactivar suscripción anterior
                suscripcion.activa = False
                suscripcion.save()

                # Crear nueva suscripción trial
                nueva_suscripcion = Suscripcion.objects.create(
                    user=user,
                    tipo="trial",
                    activa=True,
                    fecha_inicio=datetime.now().date(),
                    fecha_fin=(datetime.now() + timedelta(days=30)).date(),
                )
                print(f"✅ Nueva suscripción trial creada")
                print(f"   Fecha inicio: {nueva_suscripcion.fecha_inicio}")
                print(f"   Fecha fin: {nueva_suscripcion.fecha_fin}")
                print()
        else:
            print("✅ Suscripción activa y vigente")
            print()
    except AttributeError:
        print("❌ Usuario no tiene suscripción. Creando suscripción trial...")
        with transaction.atomic():
            suscripcion = Suscripcion.objects.create(
                user=user,
                tipo="trial",
                activa=True,
                fecha_inicio=datetime.now().date(),
                fecha_fin=(datetime.now() + timedelta(days=30)).date(),
            )
            print(f"✅ Suscripción trial creada")
            print(f"   Tipo: {suscripcion.tipo}")
            print(f"   Activa: {suscripcion.activa}")
            print(f"   Fecha inicio: {suscripcion.fecha_inicio}")
            print(f"   Fecha fin: {suscripcion.fecha_fin}")
            print()

    # 6. Verificar que puede autenticarse
    print("🔐 Verificando autenticación...")
    test_user = User.objects.get(username=username)
    if test_user.check_password(password):
        print("✅ La contraseña es correcta y el usuario puede autenticarse")
    else:
        print("❌ ERROR: La contraseña no coincide")
    print()

    # 7. Resumen final
    print("=" * 70)
    print("📋 RESUMEN FINAL")
    print("=" * 70)
    print()
    print("🔑 CREDENCIALES DE ACCESO:")
    print(f"   Usuario: {username}")
    print(f"   Contraseña: {password}")
    print(f"   Email: {user.email}")
    print()
    print("🌐 URLS DE ACCESO:")
    print("   Login USA: https://www.egarage.cl/us/accounts/login/")
    print("   Dashboard USA: https://www.egarage.cl/us/")
    print()

    try:
        empresa = user.empresa
        print("🏢 EMPRESA:")
        print(f"   Nombre: {empresa.nombre_taller}")
        print(f"   País: {empresa.pais}")
        print(f"   Moneda: {empresa.moneda or 'USD'}")
        print()
    except:
        pass

    try:
        suscripcion = user.suscripcion
        print("📋 SUSCRIPCIÓN:")
        print(f"   Tipo: {suscripcion.tipo}")
        print(f"   Estado: {'Activa' if suscripcion.activa else 'Inactiva'}")
        print(f"   Válida hasta: {suscripcion.fecha_fin}")
        print()
    except:
        pass

    print("✅ USUARIO LISTO PARA USAR")
    print("=" * 70)


if __name__ == "__main__":
    verificar_y_corregir_testuser_usa()
