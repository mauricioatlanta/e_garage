#!/usr/bin/env python
"""
Script para limpiar el cache manualmente
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.core.cache import cache
from django.contrib.auth.models import User

print("🧹 LIMPIANDO CACHE")
print("=" * 30)

# Limpiar todo el cache
cache.clear()
print("✅ Cache limpiado completamente")

# Buscar usuario y invalidar su cache específico
try:
    user = User.objects.get(username='testuser_cl')
    if hasattr(user, 'empresa'):
        empresa = user.empresa
        print(f"✅ Usuario encontrado: {user.username}")
        print(f"✅ Empresa ID: {empresa.id}")
        
        # Invalidar cache específico
        from taller.context_processors import invalidate_company_cache
        invalidate_company_cache(empresa.id, None)
        print("✅ Cache específico invalidado")
        
except User.DoesNotExist:
    print("❌ Usuario testuser_cl no encontrado")
except Exception as e:
    print(f"❌ Error: {e}")

print("🎯 Cache listo para pruebas")
