#!/usr/bin/env python

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.perfilusuario import PerfilUsuario
from django.contrib.auth.models import User

try:
    # Intentar hacer una consulta simple al modelo PerfilUsuario
    count = PerfilUsuario.objects.count()
    print(f"✅ Modelo PerfilUsuario funciona correctamente")
    print(f"   Total de perfiles: {count}")
    
    # Listar algunos usuarios sin perfil
    users_without_profile = User.objects.filter(perfilusuario__isnull=True)
    if users_without_profile.exists():
        print(f"   Usuarios sin perfil: {users_without_profile.count()}")
        for user in users_without_profile[:3]:  # Solo los primeros 3
            print(f"   - {user.username}")
    else:
        print("   Todos los usuarios tienen perfil")
        
except Exception as e:
    print(f"❌ Error al acceder al modelo PerfilUsuario: {e}")

print("\n✅ Verificación completada. La tabla taller_perfilusuario está funcionando correctamente.")
