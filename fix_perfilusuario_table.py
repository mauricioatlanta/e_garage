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
    # Crear la tabla taller_perfilusuario si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS taller_perfilusuario (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            rol VARCHAR(20) NOT NULL DEFAULT 'vendedor',
            empresa_id BIGINT NOT NULL,
            user_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (empresa_id) REFERENCES taller_empresa (id) DEFERRABLE INITIALLY DEFERRED,
            FOREIGN KEY (user_id) REFERENCES auth_user (id) DEFERRABLE INITIALLY DEFERRED
        );
    """)
    
    # Crear índices
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS taller_perfilusuario_empresa_id_7c7b5c99 
        ON taller_perfilusuario (empresa_id);
    """)
    
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS taller_perfilusuario_user_id_8b4b0c4f_uniq 
        ON taller_perfilusuario (user_id);
    """)
    
    # Commit cambios
    conn.commit()
    print("✅ Tabla 'taller_perfilusuario' creada exitosamente")
    
    # Verificar que existe la tabla
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='taller_perfilusuario';")
    if cursor.fetchone():
        print("✅ Confirmado: La tabla existe en la base de datos")
    else:
        print("❌ Error: La tabla no se creó correctamente")
        
except sqlite3.Error as e:
    print(f"❌ Error al crear la tabla: {e}")
finally:
    conn.close()
