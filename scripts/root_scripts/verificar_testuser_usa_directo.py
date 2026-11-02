#!/usr/bin/env python
"""
Script para ejecutar directamente en el shell de Django del servidor:
python manage.py shell < verificar_testuser_usa_directo.py

O ejecutar línea por línea en: python manage.py shell
"""
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from taller.models import Empresa, Suscripcion

User = get_user_model()

username = "testuser_usa"
password = "TestUSA2025!"
email = "testuser@usa-garage.com"

print("=" * 70)
print("🔍 VERIFICACIÓN Y CORRECCIÓN DE testuser_usa")
print("=" * 70)
print()

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

# 2. Resetear contraseña
print("🔑 Reseteando contraseña...")
user.set_password(password)
user.is_active = True
user.save()
print(f"✅ Contraseña reseteada a: {password}")
print(f"✅ Usuario activado: {user.is_active}")
print()

# 3. Verificar autenticación ANTES de continuar
print("🔐 Verificando autenticación...")
test_user = User.objects.get(username=username)
if test_user.check_password(password):
    print("✅ La contraseña es correcta")
else:
    print("❌ ERROR: La contraseña no coincide - Intentando de nuevo...")
    user.set_password(password)
    user.save()
    if test_user.check_password(password):
        print("✅ Contraseña corregida")
    else:
        print("❌ ERROR CRÍTICO: No se pudo establecer la contraseña")
print()

# 4. Verificar/Crear empresa
try:
    empresa = user.empresa
    print(f"✅ Empresa encontrada: {empresa.nombre_taller}")
    print(f"   País: {empresa.pais}")
    if empresa.pais != "US":
        empresa.pais = "US"
        empresa.save()
        print(f"✅ País actualizado a US")
    print()
except AttributeError:
    print("❌ Usuario no tiene empresa. Creando empresa...")
    with transaction.atomic():
        empresa = Empresa.objects.create(
            user=user,
            nombre_taller="Taller de testuser_usa",
            pais="US",
            telefono="+15551234567",
            direccion="Miami, FL, USA",
        )
        print(f"✅ Empresa creada: {empresa.nombre_taller}")
        print(f"   País: {empresa.pais}")
        print()

# 5. Verificar/Crear suscripción
try:
    suscripcion = user.suscripcion
    print(f"✅ Suscripción encontrada:")
    print(f"   Tipo: {suscripcion.tipo}")
    print(f"   Activa: {suscripcion.activa}")

    vencida = False
    if suscripcion.fecha_fin:
        vencida = suscripcion.fecha_fin < datetime.now().date()
        print(f"   Fecha fin: {suscripcion.fecha_fin}")
        print(f"   Vencida: {vencida}")

    if not suscripcion.activa or vencida:
        print("⚠️ Creando nueva suscripción trial...")
        with transaction.atomic():
            suscripcion.activa = False
            suscripcion.save()
            nueva_suscripcion = Suscripcion.objects.create(
                user=user,
                tipo="trial",
                activa=True,
                fecha_inicio=datetime.now().date(),
                fecha_fin=(datetime.now() + timedelta(days=30)).date(),
            )
            print(f"✅ Nueva suscripción creada (válida hasta {nueva_suscripcion.fecha_fin})")
    else:
        print("✅ Suscripción activa")
    print()
except AttributeError:
    print("❌ No tiene suscripción. Creando suscripción trial...")
    with transaction.atomic():
        suscripcion = Suscripcion.objects.create(
            user=user,
            tipo="trial",
            activa=True,
            fecha_inicio=datetime.now().date(),
            fecha_fin=(datetime.now() + timedelta(days=30)).date(),
        )
        print(f"✅ Suscripción creada (válida hasta {suscripcion.fecha_fin})")
        print()

# 6. Verificación final de autenticación
print("=" * 70)
print("🔐 VERIFICACIÓN FINAL DE AUTENTICACIÓN")
print("=" * 70)
final_user = User.objects.get(username=username)
if final_user.check_password(password):
    print("✅ AUTENTICACIÓN FUNCIONAL")
    print()
    print("🔑 CREDENCIALES:")
    print(f"   Usuario: {username}")
    print(f"   Contraseña: {password}")
    print()
    print("🌐 URL: https://www.egarage.cl/us/accounts/login/")
else:
    print("❌ ERROR: La autenticación aún no funciona")
    print("   Intentando método alternativo...")
    # Intentar crear usuario desde cero
    User.objects.filter(username=username).delete()
    new_user = User.objects.create_user(
        username=username, email=email, password=password, is_active=True
    )
    if new_user.check_password(password):
        print("✅ Usuario recreado exitosamente")
    else:
        print("❌ ERROR CRÍTICO: Contactar administrador")

print("=" * 70)
