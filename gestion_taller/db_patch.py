"""
db_patch.py desactivado temporalmente.

Motivo:
El monkey patch de psycopg2 estaba rompiendo conexiones PostgreSQL
en producción y ya no es necesario.

Producción ahora usa PostgreSQL correctamente vía settings_prod.py
y .env.prod.
"""

def patch_postgresql_backend():
    return False
