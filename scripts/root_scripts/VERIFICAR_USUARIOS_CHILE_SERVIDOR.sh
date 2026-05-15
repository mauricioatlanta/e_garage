#!/bin/bash
# Script para verificar usuarios de prueba de Chile en el servidor
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "🔍 Verificando usuarios de prueba de Chile..."

python3 << 'PYEOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Empresa

print("🔐 USUARIOS DE PRUEBA - CHILE")
print("=" * 60)

# Buscar usuarios relacionados con Chile
usuarios_chile = [
    'test_chile',
    'test_chile_pago',
    'testuser_cl',
    'testuser_chile',
    'admin_chile',
]

print("\n📋 Buscando usuarios de prueba...")
print()

usuarios_encontrados = []

for username in usuarios_chile:
    try:
        user = User.objects.get(username=username)
        try:
            empresa = user.empresa
            pais = empresa.pais if hasattr(empresa, 'pais') else 'N/A'
            nombre_empresa = empresa.nombre_taller if hasattr(empresa, 'nombre_taller') else empresa.nombre if hasattr(empresa, 'nombre') else 'N/A'
        except:
            empresa = None
            pais = 'N/A'
            nombre_empresa = 'Sin empresa'
        
        usuarios_encontrados.append({
            'username': username,
            'email': user.email,
            'pais': pais,
            'empresa': nombre_empresa,
            'activo': user.is_active,
        })
        
        print(f"✅ Usuario encontrado: {username}")
        print(f"   Email: {user.email}")
        print(f"   País: {pais}")
        print(f"   Empresa: {nombre_empresa}")
        print(f"   Activo: {user.is_active}")
        print()
    except User.DoesNotExist:
        print(f"❌ Usuario no encontrado: {username}")
        print()

# Mostrar credenciales conocidas
print("\n🔑 CREDENCIALES CONOCIDAS:")
print("=" * 60)
print()
print("Según la documentación del proyecto:")
print()
print("🇨🇱 CHILE - Usuario Gratuito (Trial):")
print("   Usuario: test_chile")
print("   Email: test_chile@egarage.cl")
print("   Contraseña: test1234")
print()
print("🇨🇱 CHILE - Usuario Pagado:")
print("   Usuario: test_chile_pago")
print("   Email: test_chile_pago@egarage.cl")
print("   Contraseña: test1234")
print()
print("🇨🇱 CHILE - Usuario Alternativo:")
print("   Usuario: testuser_cl")
print("   Contraseña: test123")
print()

# Verificar si algún usuario necesita reset de contraseña
if usuarios_encontrados:
    print("\n💡 Si las credenciales no funcionan, puedes resetear la contraseña:")
    print("   python manage.py changepassword <username>")
    print()
    print("   O crear un nuevo usuario de prueba con:")
    print("   python manage.py shell")
    print("   >>> from django.contrib.auth.models import User")
    print("   >>> user = User.objects.create_user('test_chile', 'test_chile@egarage.cl', 'test1234')")
else:
    print("\n⚠️  No se encontraron usuarios de prueba.")
    print("   Puedes crear uno ejecutando el script de creación de usuarios.")
PYEOF

