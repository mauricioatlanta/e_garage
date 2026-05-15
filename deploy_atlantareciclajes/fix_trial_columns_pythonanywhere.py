#!/usr/bin/env python
"""
Script para añadir la columna trial_started_at en PythonAnywhere si no existe.
Ejecutar en la consola de PythonAnywhere dentro del virtualenv.
"""
import os
import sys
import django

# Configurar Django (ajusta el nombre de tu módulo de settings si es diferente)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db import connection


def add_trial_started_at_if_missing():
    """Añade la columna trial_started_at si no existe"""
    with connection.cursor() as cursor:
        try:
            # Verificar si la columna ya existe (SQLite)
            cursor.execute("PRAGMA table_info(taller_empresa);")
            columns = [row[1] for row in cursor.fetchall()]

            if "trial_started_at" in columns:
                print("[OK] La columna 'trial_started_at' ya existe. No se requiere accion.")
                return True

            # Intentar añadir la columna
            cursor.execute("ALTER TABLE taller_empresa ADD COLUMN trial_started_at datetime;")
            print("[OK] Columna 'trial_started_at' anadida exitosamente.")
            return True

        except Exception as e:
            error_msg = str(e)
            if "duplicate column" in error_msg.lower() or "already exists" in error_msg.lower():
                print("[OK] La columna 'trial_started_at' ya existe.")
                return True
            else:
                print(f"[ERROR] Error: {error_msg}")
                print("\nSi estas usando PostgreSQL o MySQL, usa este comando SQL manualmente:")
                print("ALTER TABLE taller_empresa ADD COLUMN trial_started_at TIMESTAMP NULL;")
                return False


if __name__ == "__main__":
    success = add_trial_started_at_if_missing()
    sys.exit(0 if success else 1)
