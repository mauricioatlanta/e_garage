#!/usr/bin/env python

import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

# Conectar directamente a la base de datos SQLite
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    # Insertar registro en django_migrations para marcar la migración como aplicada
    cursor.execute("""
        INSERT INTO django_migrations (app, name, applied) 
        VALUES ('taller', '0003_fix_perfilusuario', datetime('now'));
    """)
    
    conn.commit()
    print("✅ Migración '0003_fix_perfilusuario' marcada como aplicada")
        
except sqlite3.IntegrityError as e:
    print(f"ℹ️ La migración ya está registrada: {e}")
except sqlite3.Error as e:
    print(f"❌ Error al registrar la migración: {e}")
finally:
    conn.close()
