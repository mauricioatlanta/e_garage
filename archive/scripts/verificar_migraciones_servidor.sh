#!/bin/bash
# Script para verificar migraciones en el servidor

echo "=========================================="
echo "VERIFICANDO MIGRACIONES EN EL SERVIDOR"
echo "=========================================="
echo ""

echo "1. ARCHIVOS DE MIGRACION EXISTENTES:"
ls -la taller/migrations/0*.py | grep -E "000[0-9]|0010"
echo ""

echo "2. MIGRACIONES APLICADAS EN LA BASE DE DATOS:"
python3.10 manage.py shell << EOF
from django.db import connection
cursor = connection.cursor()

# Para SQLite
if 'sqlite' in connection.settings_dict['ENGINE']:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations'")
    if cursor.fetchone():
        cursor.execute("SELECT app, name FROM django_migrations WHERE app='taller' ORDER BY name")
        rows = cursor.fetchall()
        for row in rows:
            print(f"   {row[1]}")
    else:
        print("   Tabla django_migrations no existe")
# Para MySQL
elif 'mysql' in connection.settings_dict['ENGINE']:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app='taller' ORDER BY name")
    rows = cursor.fetchall()
    for row in rows:
        print(f"   {row[1]}")
# Para PostgreSQL
else:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app='taller' ORDER BY name")
    rows = cursor.fetchall()
    for row in rows:
        print(f"   {row[1]}")
EOF

echo ""
echo "3. ULTIMA MIGRACION APLICADA:"
python3.10 manage.py shell << EOF
from django.db import connection
cursor = connection.cursor()

if 'sqlite' in connection.settings_dict['ENGINE']:
    cursor.execute("SELECT name FROM django_migrations WHERE app='taller' ORDER BY name DESC LIMIT 1")
elif 'mysql' in connection.settings_dict['ENGINE']:
    cursor.execute("SELECT name FROM django_migrations WHERE app='taller' ORDER BY name DESC LIMIT 1")
else:
    cursor.execute("SELECT name FROM django_migrations WHERE app='taller' ORDER BY name DESC LIMIT 1")

row = cursor.fetchone()
if row:
    print(f"   {row[0]}")
else:
    print("   No hay migraciones aplicadas")
EOF

echo ""
echo "=========================================="
