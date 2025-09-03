#!/usr/bin/env python
"""
Script para limpiar todo el caché relacionado con branding y configuración de empresas
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.core.cache import cache
from taller.models.empresa import Empresa
from django.contrib.auth.models import User
from taller.context_processors import invalidate_company_cache

def limpiar_cache_completo():
    """Limpia todo el caché relacionado con branding y empresas"""
    print("🧹 Limpiando caché de branding y empresas...")
    
    # Obtener todos los usuarios con empresas
    empresas = Empresa.objects.all()
    usuarios_con_empresa = User.objects.filter(
        pk__in=empresas.values_list('user_id', flat=True)
    ).exclude(id__isnull=True)
    
    cache_keys_eliminadas = 0
    
    # Limpiar caché por usuario
    for usuario in usuarios_con_empresa:
        try:
            # Usar función oficial
            invalidate_company_cache(usuario.id)
            
            # Claves adicionales que podrían existir
            claves = [
                f"company_settings_{usuario.id}",
                f"company_branding_{usuario.id}",
                f"user_company_{usuario.id}",
            ]
            
            for clave in claves:
                cache.delete(clave)
                cache_keys_eliminadas += 1
                print(f"  ✅ Cache eliminado: {clave}")
                
        except Exception as e:
            print(f"  ❌ Error con usuario {usuario.username}: {e}")
    
    # Limpiar caché por empresa
    for empresa in empresas:
        claves_empresa = [
            f"company_settings:{empresa.id}",
            f"empresa_config_{empresa.id}",
            f"branding_{empresa.id}",
        ]
        
        for clave in claves_empresa:
            cache.delete(clave)
            cache_keys_eliminadas += 1
            print(f"  ✅ Cache eliminado: {clave}")
    
    # Limpiar patrones generales
    print("🧹 Limpiando patrones generales de caché...")
    
    try:
        # Django no tiene cache.clear_pattern(), pero podemos intentar limpiar todo
        cache.clear()
        print("  ✅ Cache completo limpiado")
    except Exception as e:
        print(f"  ⚠️ No se pudo limpiar cache completo: {e}")
    
    print(f"\n📊 Resumen:")
    print(f"   - Usuarios procesados: {usuarios_con_empresa.count()}")
    print(f"   - Empresas procesadas: {empresas.count()}")
    print(f"   - Claves de cache eliminadas: {cache_keys_eliminadas}")
    print(f"\n✅ Limpieza de caché completada!")
    print(f"\n💡 Tip: Ahora recarga las páginas para ver los cambios de branding.")

if __name__ == "__main__":
    limpiar_cache_completo()
