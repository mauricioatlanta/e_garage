#!/usr/bin/env python
"""Script para verificar logos usando SQL directo"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db import connection

cursor = connection.cursor()

print("=" * 80)
print("🔍 VERIFICACIÓN DE LOGOS (SQL directo)")
print("=" * 80)

# ConfiguracionEmpresa
print("\n📊 ConfiguracionEmpresa:")
cursor.execute(
    """
    SELECT ce.empresa_id, ce.logo, e.nombre_taller, e.user_id
    FROM taller_configuracionempresa ce
    JOIN taller_empresa e ON ce.empresa_id = e.id
    WHERE ce.logo IS NOT NULL AND ce.logo != ''
"""
)
results = cursor.fetchall()
if results:
    for empresa_id, logo, nombre, user_id in results:
        print(f"  Empresa: {nombre} (ID: {empresa_id}, User ID: {user_id})")
        print(f"    Logo: {logo}")
        print(f"    URL completa: /media/{logo}")
else:
    print("  ❌ No se encontraron logos")

# Empresa directamente
print("\n📊 Empresa (directo):")
cursor.execute(
    """
    SELECT id, nombre_taller, user_id, logo
    FROM taller_empresa
    WHERE logo IS NOT NULL AND logo != ''
"""
)
results = cursor.fetchall()
if results:
    for empresa_id, nombre, user_id, logo in results:
        print(f"  Empresa: {nombre} (ID: {empresa_id}, User ID: {user_id})")
        print(f"    Logo: {logo}")
        print(f"    URL completa: /media/{logo}")
else:
    print("  ❌ No se encontraron logos")

print("\n" + "=" * 80)
