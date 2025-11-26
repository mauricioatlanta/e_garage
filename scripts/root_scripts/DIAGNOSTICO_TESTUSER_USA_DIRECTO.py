"""
Script para ejecutar directamente en Django shell del servidor
Copiar y pegar todo el contenido en: python manage.py shell
"""

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from datetime import datetime, timedelta

# Importar modelos
try:
    from taller.models import Empresa, Suscripcion
except ImportError:
    print(
        "❌ ERROR: No se pueden importar los modelos. Verifica que estés en el directorio correcto."
    )
    exit()

User = get_user_model()

# Credenciales
username = "testuser_usa"
password = "TestUSA2025!"
email = "testuser@usa-garage.com"

print("=" * 80)
print(f"🔍 DIAGNÓSTICO Y CORRECCIÓN: {username}")
print("=" * 80)
print()

# 1. Verificar/Crear usuario
try:
    user = User.objects.get(username=username)
    print(f"✅ Usuario encontrado: {user.username} (ID: {user.pk})")
    print(f"   Email: {user.email}")
    print(f"   Activo: {user.is_active}")
    print(f"   Staff: {user.is_staff}")
    print(f"   Superuser: {user.is_superuser}")
    print()
except User.DoesNotExist:
    print(f"❌ Usuario '{username}' NO EXISTE")
    print("🔧 Creando usuario...")
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username, email=email, password=password, is_active=True
            )
        print(f"✅ Usuario creado: {user.username} (ID: {user.pk})")
        print()
    except Exception as e:
        print(f"❌ ERROR al crear usuario: {e}")
        exit()

# 2. Verificar/Resetear contraseña
print("🔑 Verificando contraseña...")
password_valida = user.check_password(password)
print(f"   Contraseña esperada: {password}")
print(f"   Estado actual: {'✅ CORRECTA' if password_valida else '❌ INCORRECTA'}")
print()

if not password_valida:
    print("🔧 Reseteando contraseña...")
    try:
        with transaction.atomic():
            user.set_password(password)
            user.is_active = True
            user.save()
        user.refresh_from_db()
        password_valida_after = user.check_password(password)
        if password_valida_after:
            print("✅ Contraseña reseteada exitosamente")
        else:
            print("❌ ERROR: No se pudo resetear la contraseña")
    except Exception as e:
        print(f"❌ ERROR al resetear contraseña: {e}")
    print()
else:
    # Asegurar que esté activo
    if not user.is_active:
        print("🔧 Activando usuario...")
        with transaction.atomic():
            user.is_active = True
            user.save()
        print("✅ Usuario activado")
        print()

# 3. Verificar/Crear empresa
print("🏢 Verificando empresa...")
try:
    empresa = user.empresa
    print(f"✅ Empresa encontrada: {empresa.nombre_taller} (ID: {empresa.pk})")
    print(f"   País: {empresa.pais}")
    try:
        print(f"   Moneda: {empresa.moneda}")
    except AttributeError:
        print(f"   Moneda: No definida")

    # Verificar/Corregir país
    if empresa.pais != "US":
        print(f"⚠️  País incorrecto ({empresa.pais}). Corrigiendo a US...")
        with transaction.atomic():
            empresa.pais = "US"
            if hasattr(empresa, "moneda"):
                empresa.moneda = "USD"
            empresa.save()
        print("✅ País corregido a US")
    print()
except AttributeError:
    print("❌ Usuario no tiene empresa asociada")
    print("🔧 Creando empresa...")
    try:
        with transaction.atomic():
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller="Taller de testuser_usa",
                pais="US",
                telefono="+15551234567",
            )
            if hasattr(empresa, "moneda"):
                empresa.moneda = "USD"
                empresa.save()
        print(f"✅ Empresa creada: {empresa.nombre_taller} (ID: {empresa.pk})")
        print(f"   País: {empresa.pais}")
        print()
    except Exception as e:
        print(f"❌ ERROR al crear empresa: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        print()

# 4. Verificar/Crear suscripción
print("📋 Verificando suscripción...")
try:
    suscripcion = user.suscripcion
    print(f"✅ Suscripción encontrada: {suscripcion.tipo} (ID: {suscripcion.pk})")
    print(f"   Activa: {suscripcion.activa}")
    print(f"   Fecha inicio: {suscripcion.fecha_inicio}")
    print(f"   Fecha fin: {suscripcion.fecha_fin}")

    # Verificar si está vencida
    if suscripcion.fecha_fin:
        vencida = suscripcion.fecha_fin < datetime.now().date()
        vigente = "❌ VENCIDA" if vencida else "✅ VIGENTE"
        print(f"   Estado: {vigente}")

    # Corregir si está inactiva o vencida
    if not suscripcion.activa or (
        suscripcion.fecha_fin and suscripcion.fecha_fin < datetime.now().date()
    ):
        print("⚠️  Suscripción inactiva o vencida. Renovando...")
        with transaction.atomic():
            suscripcion.activa = True
            suscripcion.fecha_inicio = datetime.now().date()
            suscripcion.fecha_fin = (datetime.now() + timedelta(days=30)).date()
            if hasattr(suscripcion, "estado"):
                suscripcion.estado = "activa"
            suscripcion.save()
        print(f"✅ Suscripción renovada hasta {suscripcion.fecha_fin}")
    print()
except AttributeError:
    print("❌ Usuario no tiene suscripción asociada")
    print("🔧 Creando suscripción...")
    try:
        with transaction.atomic():
            suscripcion_data = {
                "user": user,
                "tipo": "trial",
                "fecha_inicio": datetime.now().date(),
                "fecha_fin": (datetime.now() + timedelta(days=30)).date(),
                "activa": True,
            }
            if hasattr(Suscripcion, "estado"):
                suscripcion_data["estado"] = "activa"

            suscripcion = Suscripcion.objects.create(**suscripcion_data)
        print(f"✅ Suscripción creada: {suscripcion.tipo} hasta {suscripcion.fecha_fin}")
        print()
    except Exception as e:
        print(f"❌ ERROR al crear suscripción: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        print()

# 5. Verificar autenticación Django
print("🔐 Verificando autenticación Django...")
try:
    auth_user = authenticate(username=username, password=password)
    if auth_user:
        print("✅ Autenticación Django: EXITOSA")
        print(f"   Usuario autenticado: {auth_user.username} (ID: {auth_user.pk})")
    else:
        print("❌ Autenticación Django: FALLIDA")
        print("   Posibles causas:")
        print("   - Usuario inactivo")
        print("   - Contraseña incorrecta")
        print("   - Problema con AUTHENTICATION_BACKENDS")
        print()
        print("   Verificando estado del usuario:")
        user.refresh_from_db()
        print(f"   - Usuario activo: {user.is_active}")
        print(f"   - Contraseña verificada con check_password: {user.check_password(password)}")
except Exception as e:
    print(f"❌ ERROR al verificar autenticación: {e}")
    import traceback

    traceback.print_exc()
print()

# 6. Resumen final
print("=" * 80)
print("✅ RESUMEN FINAL")
print("=" * 80)
print(f"Usuario: {username}")
print(f"Contraseña: {password}")
print(f"Email: {user.email}")
print(f"Usuario activo: {'✅ Sí' if user.is_active else '❌ No'}")
try:
    print(f"Empresa: {user.empresa.nombre_taller}, País: {user.empresa.pais}")
except:
    print("Empresa: ❌ No asociada")
try:
    print(f"Suscripción: {user.suscripcion.tipo}, Activa: {user.suscripcion.activa}")
except:
    print("Suscripción: ❌ No asociada")
print()
print("🔗 URLs de prueba:")
print("   - Login: https://www.egarage.cl/us/accounts/login/")
print("   - Dashboard: https://www.egarage.cl/us/dashboard/")
print("=" * 80)
