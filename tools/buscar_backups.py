#!/usr/bin/env python
"""
Script para buscar archivos de backup que puedan contener datos de suscripciones
"""

import os
import glob
from pathlib import Path

# Directorios comunes donde pueden estar los backups
directorios_buscar = [
    '/home/atlantareciclajes',
    '/home/atlantareciclajes/apps/egarage',
    '/home/atlantareciclajes/apps/egarage/current',
    '/home/atlantareciclajes/apps/egarage/releases',
    '~/backups',
    '~/db_backups',
    '~/database_backups',
]

# Patrones de archivos de backup
patrones = [
    '*.sql',
    '*.sqlite3',
    '*.db',
    '*backup*.sql',
    '*backup*.db',
    '*suscripcion*.sql',
    '*suscripcion*.json',
    '*export*.sql',
    '*export*.json',
    '*dump*.sql',
    '*.bak',
]

print("="*80)
print("BÚSQUEDA DE BACKUPS")
print("="*80)
print()

archivos_encontrados = []

for directorio in directorios_buscar:
    dir_expandido = os.path.expanduser(directorio)
    if os.path.exists(dir_expandido):
        print(f"Buscando en: {dir_expandido}")
        for patron in patrones:
            # Buscar recursivamente
            for root, dirs, files in os.walk(dir_expandido):
                for file in files:
                    if any(patron.replace('*', '') in file.lower() for patron in patrones if '*' in patron) or file.endswith(tuple(patron.replace('*', '') for patron in patrones if not '*' in patron)):
                        ruta_completa = os.path.join(root, file)
                        tamaño = os.path.getsize(ruta_completa)
                        fecha_mod = os.path.getmtime(ruta_completa)
                        archivos_encontrados.append({
                            'ruta': ruta_completa,
                            'tamaño': tamaño,
                            'fecha': fecha_mod
                        })
                        print(f"  ✓ {ruta_completa} ({tamaño} bytes)")

print()
print("="*80)
print("ARCHIVOS DE BASE DE DATOS")
print("="*80)

# Buscar archivos .sqlite3 o .db
for root, dirs, files in os.walk('/home/atlantareciclajes'):
    for file in files:
        if file.endswith(('.sqlite3', '.db', '.sql')):
            ruta = os.path.join(root, file)
            tamaño = os.path.getsize(ruta)
            print(f"  - {ruta} ({tamaño} bytes)")
