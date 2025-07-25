#!/usr/bin/env python

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Listar todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tablas en la base de datos:")
for table in tables:
    print(f"  - {table[0]}")

# Verificar si existe la tabla taller_perfilusuario
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='taller_perfilusuario';")
perfil_table = cursor.fetchone()

if perfil_table:
    print("\n✅ La tabla 'taller_perfilusuario' existe")
    
    # Verificar la estructura de la tabla
    cursor.execute("PRAGMA table_info(taller_perfilusuario);")
    columns = cursor.fetchall()
    print("Columnas de la tabla:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
else:
    print("\n❌ La tabla 'taller_perfilusuario' NO existe")

conn.close()
