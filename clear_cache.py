#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.core.cache import cache

print("🧹 Limpiando cache...")
cache.clear()
print("✅ Cache limpiado!")
