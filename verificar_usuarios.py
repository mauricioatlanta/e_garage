#!/usr/bin/env python3
"""
Verificar y crear usuario admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User

print('👤 === VERIFICAR USUARIO ADMIN ===')

try:
    admin = User.objects.get(username='admin')
    print(f'✅ Usuario admin existe: {admin.username}')
    print(f'   - Email: {admin.email}')
    print(f'   - Superuser: {admin.is_superuser}')
    print(f'   - Staff: {admin.is_staff}')
    print(f'   - Activo: {admin.is_active}')
    
    # Verificar contraseña
    if admin.check_password('admin123'):
        print('✅ Contraseña admin123 es correcta')
    else:
        print('❌ Contraseña admin123 es incorrecta')
        print('🔧 Estableciendo nueva contraseña...')
        admin.set_password('admin123')
        admin.save()
        print('✅ Contraseña actualizada a admin123')
        
except User.DoesNotExist:
    print('❌ Usuario admin no existe')
    print('🔧 Creando usuario admin...')
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@ejemplo.com',
        password='admin123'
    )
    print('✅ Usuario admin creado')

print()
print('🔑 === VERIFICAR USUARIO TALLER2 ===')

try:
    taller2 = User.objects.get(username='taller2')
    print(f'✅ Usuario taller2 existe: {taller2.username}')
    
    # Verificar contraseña
    if taller2.check_password('taller2123'):
        print('✅ Contraseña taller2123 es correcta')
    else:
        print('❌ Contraseña taller2123 es incorrecta')
        print('🔧 Estableciendo nueva contraseña...')
        taller2.set_password('taller2123')
        taller2.save()
        print('✅ Contraseña actualizada a taller2123')
        
except User.DoesNotExist:
    print('❌ Usuario taller2 no existe')

print()
print('🏁 === VERIFICACIÓN COMPLETADA ===')
