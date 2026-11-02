#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models import Cliente, Documento, Empresa, Repuesto, Vehiculo

print("\n" + "=" * 60)
print("          LIMPIANDO BASE DE DATOS")
print("=" * 60 + "\n")

# Eliminar todos los registros relacionados primero
print("🗑️  Eliminando registros relacionados...")

# Documentos
docs_count = Documento.objects.all().count()
if docs_count > 0:
    Documento.objects.all().delete()
    print(f"   ✅ {docs_count} documentos eliminados")

# Repuestos
rep_count = Repuesto.objects.all().count()
if rep_count > 0:
    Repuesto.objects.all().delete()
    print(f"   ✅ {rep_count} repuestos eliminados")

# Vehículos
veh_count = Vehiculo.objects.all().count()
if veh_count > 0:
    Vehiculo.objects.all().delete()
    print(f"   ✅ {veh_count} vehículos eliminados")

# Clientes
cli_count = Cliente.objects.all().count()
if cli_count > 0:
    Cliente.objects.all().delete()
    print(f"   ✅ {cli_count} clientes eliminados")

# Empresas
emp_count = Empresa.objects.all().count()
if emp_count > 0:
    Empresa.objects.all().delete()
    print(f"   ✅ {emp_count} empresas eliminadas")

print()

# Ahora eliminar usuarios no-superuser
users_to_delete = User.objects.filter(is_superuser=False)
count = users_to_delete.count()
if count > 0:
    print(f"🗑️  Eliminando {count} usuarios de prueba...")
    users_to_delete.delete()
    print(f"✅ {count} usuarios eliminados correctamente\n")

# Verificar usuarios restantes
remaining = User.objects.all()
print(f"👥 Usuarios restantes: {remaining.count()}")
for u in remaining:
    print(f'   - {u.username} ({"Superuser" if u.is_superuser else "Normal"})')

print("\n" + "=" * 60)
print("          CREANDO CUENTAS DE PRUEBA")
print("=" * 60 + "\n")

# Crear cuenta de prueba para CHILE
try:
    user_chile = User.objects.create_user(
        username="chile_test",
        email="chile@test.com",
        password="Chile2024!",
        first_name="Usuario",
        last_name="Chile",
    )
    print("✅ Cuenta CHILE creada:")
    print("   Username: chile_test")
    print("   Email: chile@test.com")
    print("   Password: Chile2024!")
    print("   País: 🇨🇱 Chile\n")

    # Crear empresa para Chile
    empresa_chile = Empresa.objects.create(
        usuario=user_chile,
        nombre="Taller Chile Test",
        pais="CL",
        telefono="+56912345678",
        direccion="Santiago, Chile",
        rut="12345678-9",
        estado_suscripcion="activo",
    )
    print(f"   ✅ Empresa creada: {empresa_chile.nombre}")
    print(f"   ✅ Estado: {empresa_chile.estado_suscripcion}\n")

except Exception as e:
    print(f"❌ Error creando usuario Chile: {e}\n")

# Crear cuenta de prueba para USA
try:
    user_usa = User.objects.create_user(
        username="usa_test",
        email="usa@test.com",
        password="Usa2024!",
        first_name="User",
        last_name="USA",
    )
    print("✅ Cuenta USA creada:")
    print("   Username: usa_test")
    print("   Email: usa@test.com")
    print("   Password: Usa2024!")
    print("   País: 🇺🇸 USA\n")

    # Crear empresa para USA
    empresa_usa = Empresa.objects.create(
        usuario=user_usa,
        nombre="USA Garage Test",
        pais="US",
        telefono="+14155551234",
        direccion="California, USA",
        rut="123-45-6789",
        estado_suscripcion="activo",
    )
    print(f"   ✅ Empresa creada: {empresa_usa.nombre}")
    print(f"   ✅ Estado: {empresa_usa.estado_suscripcion}\n")

except Exception as e:
    print(f"❌ Error creando usuario USA: {e}\n")

print("=" * 60)
print("          RESUMEN FINAL")
print("=" * 60 + "\n")

all_users = User.objects.all()
print(f"👥 Total usuarios en sistema: {all_users.count()}\n")

for user in all_users:
    print(f'{"🔑" if user.is_superuser else "👤"} {user.username}')
    print(f"   Email: {user.email}")
    if user.is_superuser:
        print("   Tipo: Superuser (Admin)")
    else:
        try:
            empresa = user.empresa
            print(f"   Empresa: {empresa.nombre}")
            print(f'   País: {"🇨🇱 Chile" if empresa.pais == "CL" else "🇺🇸 USA"}')
            print(f"   Estado: {empresa.estado_suscripcion}")
        except:
            print("   Sin empresa")
    print()

print("=" * 60)
print("\n✅ CUENTAS DE PRUEBA LISTAS PARA USAR:\n")
print("🇨🇱 CHILE:")
print("   URL: http://127.0.0.1:8000/accounts/login/")
print("   Username: chile_test")
print("   Password: Chile2024!\n")
print("🇺🇸 USA:")
print("   URL: http://127.0.0.1:8000/accounts/login/")
print("   Username: usa_test")
print("   Password: Usa2024!\n")
print("=" * 60 + "\n")
