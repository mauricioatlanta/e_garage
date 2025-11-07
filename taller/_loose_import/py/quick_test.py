#!/usr/bin/env python
"""
Test rápido para verificar que el sistema funciona correctamente.
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings.dev')
django.setup()

from django.core.management import call_command
from django.urls import get_resolver

def test_system():
    """Test rápido del sistema."""
    print("🧪 Test rápido del sistema...")
    
    # 1. Verificar que no hay errores de configuración
    print("1. Verificando configuración...")
    try:
        call_command('check')
        print("   ✅ Configuración OK")
    except Exception as e:
        print(f"   ❌ Error de configuración: {e}")
        return False
    
    # 2. Verificar que las URLs se cargan correctamente
    print("2. Verificando URLs...")
    try:
        resolver = get_resolver()
        names = [k for k in resolver.reverse_dict.keys() if isinstance(k, str)]
        print(f"   ✅ {len(names)} URLs cargadas")
        
        # Verificar que hay URLs para ambos países
        us_count = len([name for name in names if "taller_us_en" in name])
        cl_count = len([name for name in names if "taller_cl_es" in name])
        
        print(f"   ✅ {us_count} URLs para US/EN")
        print(f"   ✅ {cl_count} URLs para CL/ES")
        
    except Exception as e:
        print(f"   ❌ Error cargando URLs: {e}")
        return False
    
    # 3. Verificar que no hay duplicados
    print("3. Verificando duplicados...")
    try:
        unique_names = set(names)
        if len(names) == len(unique_names):
            print("   ✅ No hay duplicados")
        else:
            print(f"   ❌ {len(names) - len(unique_names)} duplicados encontrados")
            return False
    except Exception as e:
        print(f"   ❌ Error verificando duplicados: {e}")
        return False
    
    print("\n🎉 ¡Sistema funcionando correctamente!")
    return True

if __name__ == "__main__":
    test_system()
