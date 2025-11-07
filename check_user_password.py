#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# Verificar usuario testuser_usa
print("=== VERIFICANDO USUARIO testuser_usa ===")
try:
    user = User.objects.get(username='testuser_usa')
    print(f"Usuario: {user.username}")
    print(f"Email: {user.email}")
    print(f"Es activo: {user.is_active}")
    print(f"Es staff: {user.is_staff}")
    print(f"Es superuser: {user.is_superuser}")
    
    # Probar autenticación con diferentes contraseñas
    passwords_to_try = ['testpass123', 'testuser123', 'password', 'admin', 'test']
    
    for password in passwords_to_try:
        auth_user = authenticate(username='testuser_usa', password=password)
        if auth_user:
            print(f"✅ Contraseña correcta: {password}")
            break
        else:
            print(f"❌ Contraseña incorrecta: {password}")
    
    # Si ninguna contraseña funciona, crear una nueva
    if not any(authenticate(username='testuser_usa', password=p) for p in passwords_to_try):
        print("\n=== CREANDO NUEVA CONTRASEÑA ===")
        user.set_password('testpass123')
        user.save()
        print("✅ Nueva contraseña establecida: testpass123")
        
        # Verificar que funciona
        auth_user = authenticate(username='testuser_usa', password='testpass123')
        if auth_user:
            print("✅ Autenticación exitosa con nueva contraseña")
        else:
            print("❌ Error en autenticación con nueva contraseña")
            
except User.DoesNotExist:
    print("❌ Usuario testuser_usa no existe")
