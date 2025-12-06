#!/usr/bin/env python
"""
Script para limpiar el caché de templates y forzar recarga
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.core.cache import cache
from django.template.loaders.cached import Loader

print("🧹 Limpiando caché de Django...")

# Limpiar caché general
cache.clear()
print("✅ Cache general limpiado")

# Limpiar caché de templates si existe
try:
    # Django no cachea templates por defecto en desarrollo, pero verificar
    if hasattr(Loader, "reset"):
        Loader.reset()
        print("✅ Cache de templates limpiado")
except Exception as e:
    print(f"⚠️  No se pudo limpiar cache de templates: {e}")

print("\n📋 Instrucciones:")
print("1. Reinicia el servidor Django (Ctrl+C y vuelve a ejecutar 'python manage.py runserver')")
print("2. En el navegador, presiona Ctrl+Shift+R (o Cmd+Shift+R en Mac) para hacer hard refresh")
print("3. O abre las herramientas de desarrollador (F12) y desactiva el caché temporalmente")
print("\n✅ Listo! Los cambios deberían verse ahora.")



