#!/usr/bin/env python3
"""
Script para eliminar completamente el usuario damarysuezmeneses@gmail.com
y todos sus datos relacionados para permitir un nuevo registro de prueba.

⚠️  ADVERTENCIA: Este script elimina TODOS los datos del usuario.
Ejecutar en el servidor: python3.10 borrar_usuario_damarys.py
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.insert(0, "/home/atlantareciclajes/apps/egarage/current")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
django.setup()

from django.contrib.auth.models import User
from django.db import transaction, connection

print("=" * 70)
print("ELIMINACION DE USUARIO: damarysuezmeneses@gmail.com")
print("=" * 70)
print()
print("⚠️  ADVERTENCIA: Este script eliminará TODOS los datos del usuario.")
print()

email = "damarysuezmeneses@gmail.com"

# Buscar usuario
try:
    usuario = User.objects.filter(email=email).first()

    if not usuario:
        print(f"❌ Usuario NO encontrado: {email}")
        print("   No hay nada que eliminar.")
        sys.exit(0)

    print(f"✅ Usuario encontrado:")
    print(f"   ID: {usuario.id}")
    print(f"   Email: {usuario.email}")
    print(f"   Username: {usuario.username}")
    print()

    # Confirmar eliminación
    print("¿Estás seguro de que quieres eliminar este usuario y TODOS sus datos?")
    print("Esto incluye:")
    print("  - Usuario (User)")
    print("  - Empresa (Empresa)")
    print("  - CompanySettings")
    print("  - Suscripciones")
    print("  - EmailAddress (Allauth)")
    print("  - Todos los datos relacionados (cascada)")
    print()

    # En modo no interactivo, proceder automáticamente
    confirmar = True  # Cambiar a False si quieres confirmación interactiva

    if not confirmar:
        respuesta = input("Escribe 'SI' para confirmar: ")
        if respuesta != "SI":
            print("❌ Eliminación cancelada.")
            sys.exit(0)

    print("🔄 Iniciando eliminación...")
    print()

    # Eliminar en transacción para asegurar consistencia
    with transaction.atomic():
        # 1. Eliminar EmailAddress (Allauth) primero
        try:
            from allauth.account.models import EmailAddress

            email_addresses = EmailAddress.objects.filter(email=email)
            count = email_addresses.count()
            email_addresses.delete()
            print(f"✅ Eliminados {count} EmailAddress(es)")
        except Exception as e:
            print(f"⚠️  Error al eliminar EmailAddress: {e}")

        # 2. Eliminar CompanySettings (si existe)
        try:
            if hasattr(usuario, "company_settings"):
                usuario.company_settings.delete()
                print(f"✅ Eliminado CompanySettings")
        except Exception as e:
            print(f"⚠️  Error al eliminar CompanySettings: {e}")

        # 3. Eliminar Empresa (esto eliminará en cascada suscripciones, etc.)
        try:
            if hasattr(usuario, "empresa"):
                empresa = usuario.empresa
                empresa_id = empresa.id
                empresa.delete()
                print(f"✅ Eliminada Empresa (ID: {empresa_id})")
        except Exception as e:
            print(f"⚠️  Error al eliminar Empresa: {e}")

        # 4. Eliminar cualquier otro dato relacionado usando raw SQL
        # (por si hay datos huérfanos)
        try:
            cursor = connection.cursor()

            # Eliminar de taller_companysettings si existe
            cursor.execute(
                """
                DELETE FROM taller_companysettings 
                WHERE user_id = ?
            """,
                [usuario.id],
            )
            deleted = cursor.rowcount
            if deleted > 0:
                print(f"✅ Eliminados {deleted} registros de taller_companysettings")

            # Eliminar de taller_empresa si existe
            cursor.execute(
                """
                DELETE FROM taller_empresa 
                WHERE user_id = ?
            """,
                [usuario.id],
            )
            deleted = cursor.rowcount
            if deleted > 0:
                print(f"✅ Eliminados {deleted} registros de taller_empresa")

        except Exception as e:
            print(f"⚠️  Error al limpiar datos con SQL: {e}")

        # 5. Finalmente, eliminar el usuario
        usuario_id = usuario.id
        usuario_username = usuario.username
        usuario.delete()
        print(f"✅ Eliminado Usuario (ID: {usuario_id}, Username: {usuario_username})")

    print()
    print("=" * 70)
    print("✅ ELIMINACION COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print()
    print("El usuario y todos sus datos han sido eliminados.")
    print("Ahora puedes intentar registrarse de nuevo con el mismo email.")
    print()

    # Verificar que se eliminó
    usuario_verificacion = User.objects.filter(email=email).first()
    if usuario_verificacion:
        print("⚠️  ADVERTENCIA: El usuario aún existe después de la eliminación.")
        print("   Puede haber un problema con las relaciones en cascada.")
    else:
        print("✅ Verificación: Usuario eliminado correctamente.")

except Exception as e:
    print(f"❌ Error durante la eliminación: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
