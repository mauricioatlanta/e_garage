#!/bin/bash
# Script simplificado para crear usuario de Chile
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "🔧 Creando usuario de prueba de Chile..."

python3 << 'PYEOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction

# Intentar importar Empresa
try:
    from taller.models import Empresa
    tiene_empresa = True
except ImportError:
    tiene_empresa = False
    print("⚠️  No se pudo importar Empresa, solo se creará el usuario")

username = 'test_chile'
email = 'test_chile@egarage.cl'
password = 'test1234'

print("🔧 Creando usuario...")

with transaction.atomic():
    # Crear usuario
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        user.set_password(password)
        user.email = email
        user.is_active = True
        user.save()
        print(f"✅ Usuario {username} actualizado")
    else:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Test',
            last_name='Chile',
            is_active=True
        )
        print(f"✅ Usuario {username} creado")
    
    # Verificar autenticación
    auth_user = authenticate(username=username, password=password)
    if auth_user:
        print("✅ Autenticación verificada correctamente")
    else:
        print("⚠️  Error en autenticación")
    
    # Intentar crear empresa si el modelo existe
    if tiene_empresa:
        try:
            empresa = user.empresa
            print(f"✅ Empresa existente: {empresa}")
        except:
            try:
                # Intentar con diferentes atributos
                empresa = Empresa.objects.create(
                    usuario=user,
                    nombre='eGarage Chile Test',
                    email=email,
                    pais='CL'
                )
                print("✅ Empresa creada")
            except Exception as e1:
                try:
                    empresa = Empresa.objects.create(
                        user=user,
                        nombre_taller='eGarage Chile Test',
                        email=email,
                        pais='CL'
                    )
                    print("✅ Empresa creada (método alternativo)")
                except Exception as e2:
                    print(f"⚠️  No se pudo crear empresa: {e2}")
    
    print()
    print("=" * 70)
    print("🔑 CREDENCIALES DE ACCESO")
    print("=" * 70)
    print(f"Usuario: {username}")
    print(f"Email: {email}")
    print(f"Contraseña: {password}")
    print()
    print("🌐 Login: https://www.egarage.cl/accounts/login/")
    print("=" * 70)
PYEOF

echo "✅ Proceso completado"

