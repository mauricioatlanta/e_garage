#!/bin/bash
# Script para crear/resetear usuario de prueba de Chile funcional
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "🔧 Creando/Reseteando usuario de prueba de Chile..."

python3 << 'PYEOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from taller.models import Empresa, TrialRegistro
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

# Credenciales que vamos a crear/resetear
username = 'test_chile'
email = 'test_chile@egarage.cl'
password = 'test1234'

print("🔍 Verificando usuario existente...")

try:
    with transaction.atomic():
        # Verificar si el usuario existe
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            print(f"✅ Usuario {username} existe")
            print(f"   Email actual: {user.email}")
            print(f"   Activo: {user.is_active}")
            
            # Resetear contraseña
            user.set_password(password)
            user.email = email
            user.is_active = True
            user.save()
            print(f"✅ Contraseña reseteada a: {password}")
            
            # Verificar autenticación
            auth_user = authenticate(username=username, password=password)
            if auth_user:
                print("✅ Autenticación verificada correctamente")
            else:
                print("⚠️  La autenticación falló después del reset")
        else:
            # Crear nuevo usuario
            print(f"📝 Creando nuevo usuario: {username}")
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Test',
                last_name='Chile',
                is_active=True
            )
            print(f"✅ Usuario creado")
            
            # Verificar autenticación
            auth_user = authenticate(username=username, password=password)
            if auth_user:
                print("✅ Autenticación verificada correctamente")
            else:
                print("⚠️  La autenticación falló")
        
        # Verificar/crear empresa
        try:
            empresa = user.empresa
            print(f"✅ Empresa existente: {empresa.nombre_taller if hasattr(empresa, 'nombre_taller') else empresa.nombre}")
            
            # Asegurar que la empresa esté activa
            if hasattr(empresa, 'suscripcion_activa'):
                empresa.suscripcion_activa = True
            if hasattr(empresa, 'estado'):
                empresa.estado = 'trial'
            if hasattr(empresa, 'fecha_expiracion'):
                empresa.fecha_expiracion = timezone.now().date() + timedelta(days=30)
            empresa.save()
            print("✅ Empresa actualizada y activa")
        except Exception as e:
            print(f"⚠️  No se encontró empresa: {e}")
            print("📝 Creando empresa...")
            
            # Intentar crear empresa con diferentes atributos posibles
            try:
                empresa = Empresa.objects.create(
                    usuario=user,
                    nombre='eGarage Chile Test',
                    email=email,
                    pais='CL',
                    plan_suscripcion='gratuito',
                    fecha_inicio=timezone.now().date(),
                    fecha_expiracion=timezone.now().date() + timedelta(days=30),
                    suscripcion_activa=True,
                    estado='trial'
                )
                print("✅ Empresa creada (método 1)")
            except Exception as e1:
                try:
                    # Intentar con nombre_taller en lugar de nombre
                    empresa = Empresa.objects.create(
                        user=user,
                        nombre_taller='eGarage Chile Test',
                        email=email,
                        pais='CL',
                        plan_suscripcion='gratuito',
                        fecha_inicio=timezone.now().date(),
                        fecha_expiracion=timezone.now().date() + timedelta(days=30),
                        suscripcion_activa=True,
                        estado='trial'
                    )
                    print("✅ Empresa creada (método 2)")
                except Exception as e2:
                    print(f"⚠️  Error creando empresa: {e2}")
                    empresa = None
        
        # Crear trial si no existe
        if empresa:
            if not TrialRegistro.objects.filter(empresa=empresa).exists():
                try:
                    TrialRegistro.objects.create(
                        nombre='Test Chile',
                        email=email,
                        telefono='+56912345678',
                        empresa=empresa,
                        fecha_inicio=timezone.now().date(),
                        fecha_fin=timezone.now().date() + timedelta(days=30),
                        activo=True
                    )
                    print("✅ Trial registrado")
                except Exception as e:
                    print(f"⚠️  No se pudo crear trial: {e}")
        
        print()
        print("=" * 70)
        print("🔑 CREDENCIALES DE ACCESO - CHILE")
        print("=" * 70)
        print(f"Usuario: {username}")
        print(f"Email: {email}")
        print(f"Contraseña: {password}")
        print()
        print("🌐 URL de Login:")
        print("https://www.egarage.cl/accounts/login/")
        print("   o")
        print("https://www.egarage.cl/cl/accounts/login/")
        print()
        print("💡 También puedes usar el email como usuario:")
        print(f"Email: {email}")
        print(f"Contraseña: {password}")
        print("=" * 70)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo "✅ Proceso completado"

