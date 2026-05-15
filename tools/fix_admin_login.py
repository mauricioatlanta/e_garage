#!/usr/bin/env python
"""
Script para diagnosticar y corregir problemas de login del admin
"""

import os
import sys
import django

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from allauth.account.models import EmailAddress
from django.conf import settings

print("="*80)
print("DIAGNÓSTICO DE LOGIN DEL ADMIN")
print("="*80)

# 1. Verificar usuario admin
try:
    admin = User.objects.get(username='admin')
    print(f"\n✓ Usuario 'admin' existe")
    print(f"  Email: {admin.email}")
    print(f"  Activo: {admin.is_active}")
    print(f"  Staff: {admin.is_staff}")
    print(f"  Superuser: {admin.is_superuser}")
except User.DoesNotExist:
    print("\n✗ Usuario 'admin' no existe")
    sys.exit(1)

# 2. Verificar autenticación
print("\n" + "="*80)
print("PRUEBA DE AUTENTICACIÓN")
print("="*80)

# Probar con username
user1 = authenticate(username='admin', password='admin123')
print(f"Autenticación con username 'admin': {'✓ OK' if user1 else '✗ FALLA'}")

# Probar con email
user2 = authenticate(username=admin.email, password='admin123')
print(f"Autenticación con email '{admin.email}': {'✓ OK' if user2 else '✗ FALLA'}")

# 3. Verificar email en allauth
print("\n" + "="*80)
print("ESTADO EN ALLAUTH")
print("="*80)
try:
    email_addr = EmailAddress.objects.get(user=admin, email=admin.email)
    print(f"Email en allauth: {email_addr.email}")
    print(f"Verificado: {email_addr.verified}")
    print(f"Primario: {email_addr.primary}")
    
    if not email_addr.verified:
        print("\n⚠️ Email no verificado. Verificándolo...")
        email_addr.verified = True
        email_addr.primary = True
        email_addr.save()
        print("✓ Email verificado")
except EmailAddress.DoesNotExist:
    print("✗ Email no encontrado en allauth. Creándolo...")
    email_addr = EmailAddress.objects.create(
        user=admin,
        email=admin.email,
        verified=True,
        primary=True
    )
    print("✓ Email creado y verificado")

# 4. Verificar configuración
print("\n" + "="*80)
print("CONFIGURACIÓN")
print("="*80)
print(f"ACCOUNT_AUTHENTICATION_METHOD: {getattr(settings, 'ACCOUNT_AUTHENTICATION_METHOD', 'No definido')}")
print(f"ACCOUNT_EMAIL_VERIFICATION: {getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'No definido')}")
print(f"ACCOUNT_EMAIL_REQUIRED: {getattr(settings, 'ACCOUNT_EMAIL_REQUIRED', 'No definido')}")

# 5. Solución: Crear usuario alternativo sin allauth
print("\n" + "="*80)
print("SOLUCIÓN ALTERNATIVA")
print("="*80)
print("Si el login sigue fallando, puedes usar el usuario 'admin_sistema':")
try:
    admin_sistema = User.objects.get(username='admin_sistema')
    print(f"  Username: {admin_sistema.username}")
    print(f"  Es superuser: {admin_sistema.is_superuser}")
    print(f"  Es staff: {admin_sistema.is_staff}")
    
    # Resetear contraseña si es necesario
    admin_sistema.set_password('admin123')
    admin_sistema.is_active = True
    admin_sistema.is_staff = True
    admin_sistema.is_superuser = True
    admin_sistema.save()
    print(f"  ✓ Contraseña reseteada a 'admin123'")
except User.DoesNotExist:
    print("  ✗ Usuario 'admin_sistema' no existe")

print("\n" + "="*80)
print("RECOMENDACIONES")
print("="*80)
print("1. Intenta iniciar sesión con:")
print(f"   Email: {admin.email}")
print(f"   Password: admin123")
print("\n2. Si no funciona, intenta con:")
print("   Username: admin_sistema")
print("   Password: admin123")
print("\n3. Verifica en el navegador:")
print("   - Limpia cookies y caché")
print("   - Usa modo incógnito")
print("   - Verifica que la URL sea exactamente: https://egarage.cl/admin/")
