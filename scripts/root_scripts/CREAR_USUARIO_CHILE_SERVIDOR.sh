#!/bin/bash
# Script para crear usuario de prueba de Chile en el servidor
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "🔧 Creando usuario de prueba para Chile..."

python3 << 'PYEOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Empresa, TrialRegistro
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

username = 'test_chile'
email = 'test_chile@egarage.cl'
password = 'test1234'

try:
    with transaction.atomic():
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            print(f"⚠️  Usuario {username} ya existe")
            print(f"   Email: {user.email}")
            print(f"   Activo: {user.is_active}")
            
            # Resetear contraseña
            user.set_password(password)
            user.is_active = True
            user.save()
            print(f"✅ Contraseña reseteada a: {password}")
        else:
            # Crear nuevo usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Test',
                last_name='Chile',
                is_active=True
            )
            print(f"✅ Usuario creado: {username}")
        
        # Verificar/crear empresa
        try:
            empresa = user.empresa
            print(f"✅ Empresa existente: {empresa.nombre_taller if hasattr(empresa, 'nombre_taller') else empresa.nombre}")
        except:
            empresa = Empresa.objects.create(
                usuario=user,
                nombre='eGarage Chile Test',
                rut='12345678-9',
                email=email,
                telefono='+56912345678',
                direccion='Av. Providencia 1234, Santiago',
                ciudad='Santiago',
                pais='CL',
                plan_suscripcion='gratuito',
                fecha_inicio=timezone.now().date(),
                fecha_expiracion=timezone.now().date() + timedelta(days=30),
                suscripcion_activa=True,
                estado='trial'
            )
            print(f"✅ Empresa creada: {empresa.nombre}")
        
        # Verificar/crear trial
        if not TrialRegistro.objects.filter(empresa=empresa).exists():
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
        
        print()
        print("=" * 60)
        print("🔑 CREDENCIALES DE ACCESO:")
        print("=" * 60)
        print(f"Usuario: {username}")
        print(f"Email: {email}")
        print(f"Contraseña: {password}")
        print()
        print("🌐 URL de Login:")
        print("https://www.egarage.cl/accounts/login/")
        print("   o")
        print("https://www.egarage.cl/cl/accounts/login/")
        print("=" * 60)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo "✅ Proceso completado"

