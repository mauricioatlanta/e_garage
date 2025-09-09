#!/usr/bin/env python
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User

print("🔍 Verificando usuarios y empresas")
print("=" * 40)

try:
    u = User.objects.get(username='testuser_usa')
    print(f'✅ Usuario encontrado: {u.username}')
    if hasattr(u, 'empresa'):
        print(f'📊 Empresa: {u.empresa.id} - País: {u.empresa.pais}')
        print(f'📧 Email empresa: {u.empresa.email}')
        # Usar el campo correcto para el nombre
        nombre_empresa = getattr(u.empresa, 'nombre_comercial', getattr(u.empresa, 'razon_social', 'Sin nombre'))
        print(f'📍 Nombre empresa: {nombre_empresa}')
    else:
        print('❌ Usuario no tiene empresa asociada')
except User.DoesNotExist:
    print('❌ Usuario testuser_usa no existe')

print("\n🔍 Verificando todos los usuarios con empresas:")
users_with_companies = User.objects.filter(empresa__isnull=False)
for user in users_with_companies[:5]:
    nombre_empresa = getattr(user.empresa, 'nombre_comercial', getattr(user.empresa, 'razon_social', 'Sin nombre'))
    print(f"  {user.username}: {user.empresa.pais} ({nombre_empresa})")
