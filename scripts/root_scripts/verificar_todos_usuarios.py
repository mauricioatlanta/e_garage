#!/usr/bin/env python
"""
Script para ejecutar directamente en el shell de Django del servidor:
python manage.py shell < verificar_todos_usuarios.py

O ejecutar: python manage.py listar_usuarios_credenciales
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.db import transaction

User = get_user_model()

print("=" * 80)
print("🔍 LISTADO COMPLETO DE USUARIOS Y CREDENCIALES")
print("=" * 80)
print()

# Obtener todos los usuarios
usuarios = User.objects.all().order_by("username")

print(f"📊 Total de usuarios en el sistema: {usuarios.count()}")
print()

# Usuarios de prueba conocidos y sus contraseñas
credenciales_conocidas = {
    "testuser_usa": "TestUSA2025!",
    "test_usa": "test1234",
    "test_usa_pago": "test1234",
    "test_chile": "test1234",
    "test_chile_pago": "test1234",
    "testuser_cl": "test123",
    "admin_chile": "admin123",
    "admin_usa": "admin123",
    "admin": "admin123",
}

# Agrupar usuarios por país
usuarios_por_pais = {}
usuarios_sin_empresa = []

for user in usuarios:
    try:
        empresa = user.empresa
        pais = getattr(empresa, "pais", "N/A")

        if pais not in usuarios_por_pais:
            usuarios_por_pais[pais] = []
        usuarios_por_pais[pais].append((user, empresa))
    except AttributeError:
        usuarios_sin_empresa.append(user)

# Mostrar usuarios por país
print("🌍 USUARIOS POR PAÍS")
print("=" * 80)

for pais in sorted(usuarios_por_pais.keys()):
    usuarios_pais = usuarios_por_pais[pais]
    print()
    print(f"📍 {pais} ({len(usuarios_pais)} usuarios)")
    print("-" * 80)

    for user, empresa in usuarios_pais:
        estado = "✅ Activo" if user.is_active else "❌ Inactivo"
        tipo = (
            "👑 Superuser" if user.is_superuser else ("🔧 Staff" if user.is_staff else "👤 Normal")
        )

        # Verificar credenciales conocidas
        credencial = None
        password_valida = None

        if user.username in credenciales_conocidas:
            password_esperada = credenciales_conocidas[user.username]
            password_valida = user.check_password(password_esperada)
            credencial = f"{user.username} / {password_esperada}"

        print(f"{tipo} {user.username}")
        print(f"   Email: {user.email or 'Sin email'}")
        print(f"   Estado: {estado}")
        print(f"   Empresa: {empresa.nombre_taller if empresa else 'N/A'}")

        if credencial:
            if password_valida:
                print(f"   🔑 Credencial: {credencial} ✅")
            else:
                print(f"   🔑 Credencial esperada: {credencial} ❌ NO FUNCIONA")
                print(f"      ⚠️  La contraseña no coincide con la esperada")

        # Verificar suscripción
        try:
            suscripcion = user.suscripcion
            estado_suscripcion = "✅ Activa" if suscripcion.activa else "❌ Inactiva"
            print(f"   Suscripción: {suscripcion.tipo} - {estado_suscripcion}")
        except AttributeError:
            print("   ⚠️  Suscripción: No tiene")

        print()

# Mostrar usuarios sin empresa
if usuarios_sin_empresa:
    print()
    print("⚠️  USUARIOS SIN EMPRESA")
    print("-" * 80)
    for user in usuarios_sin_empresa:
        print(f"👤 {user.username} ({user.email or 'Sin email'})")

# Verificar testuser_usa específicamente
print()
print("=" * 80)
print("🔍 VERIFICACIÓN ESPECÍFICA: testuser_usa")
print("=" * 80)
print()

try:
    user = User.objects.get(username="testuser_usa")
    password_esperada = "TestUSA2025!"

    print(f"✅ Usuario encontrado: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Activo: {user.is_active}")
    print(f"   Staff: {user.is_staff}")
    print(f"   Superuser: {user.is_superuser}")
    print()

    # Verificar contraseña actual
    password_valida = user.check_password(password_esperada)
    print(f"🔑 Verificación de contraseña:")
    print(f"   Esperada: {password_esperada}")
    print(f"   Estado: {'✅ CORRECTA' if password_valida else '❌ INCORRECTA'}")
    print()

    if not password_valida:
        print("⚠️  La contraseña no es correcta. Reseteando...")
        with transaction.atomic():
            user.set_password(password_esperada)
            user.is_active = True
            user.save()

        # Verificar de nuevo
        user.refresh_from_db()
        if user.check_password(password_esperada):
            print("✅ Contraseña reseteada exitosamente")
        else:
            print("❌ ERROR: No se pudo resetear la contraseña")
        print()

    # Verificar empresa
    try:
        empresa = user.empresa
        print(f"🏢 Empresa: {empresa.nombre_taller}")
        print(f"   País: {empresa.pais}")
        print(f"   Moneda: {getattr(empresa, 'moneda', 'USD')}")
    except AttributeError:
        print("❌ Usuario no tiene empresa")
        print("   Ejecutar: python manage.py fix_testuser_usa")
        print()

    # Verificar suscripción
    try:
        suscripcion = user.suscripcion
        print(f"📋 Suscripción: {suscripcion.tipo}")
        print(f"   Activa: {'✅ Sí' if suscripcion.activa else '❌ No'}")
        if suscripcion.fecha_fin:
            vencida = suscripcion.fecha_fin < datetime.now().date()
            print(
                f"   Fecha fin: {suscripcion.fecha_fin} ({'✅ Vigente' if not vencida else '❌ Vencida'})"
            )
    except AttributeError:
        print("❌ Usuario no tiene suscripción")
        print("   Ejecutar: python manage.py fix_testuser_usa")
        print()

    # Probar autenticación
    from django.contrib.auth import authenticate

    auth_user = authenticate(username="testuser_usa", password=password_esperada)
    if auth_user:
        print("✅ Autenticación Django: EXITOSA")
    else:
        print("❌ Autenticación Django: FALLIDA")
        print("   El usuario existe pero la autenticación falla")

except User.DoesNotExist:
    print("❌ Usuario 'testuser_usa' NO existe")
    print()
    print("🔧 Para crear el usuario:")
    print("   python manage.py fix_testuser_usa")
    print()

# Resumen de credenciales conocidas
print()
print("=" * 80)
print("📋 RESUMEN DE CREDENCIALES CONOCIDAS")
print("=" * 80)
print()

print("🇺🇸 USA:")
print("   testuser_usa / TestUSA2025!")
print("   test_usa / test1234")
print("   test_usa_pago / test1234")
print("   admin_usa / admin123")
print()

print("🇨🇱 CHILE:")
print("   test_chile / test1234")
print("   test_chile_pago / test1234")
print("   testuser_cl / test123")
print("   admin_chile / admin123")
print()

print("🌍 ADMIN:")
print("   admin / admin123")
print()

print("=" * 80)
