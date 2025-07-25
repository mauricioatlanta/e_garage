#!/usr/bin/env python3
"""
Diagnóstico de problemas con empresa/usuario
"""
import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

print("=== DIAGNÓSTICO EMPRESA/USUARIO ===")

# 1. Verificar estructura de tabla
print("\n1. Estructura tabla empresa:")
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    cursor.execute('PRAGMA table_info(taller_empresa)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
except Exception as e:
    print(f"Error: {e}")

# 2. Verificar contenido tabla empresa
print("\n2. Contenido tabla empresa:")
try:
    cursor.execute('SELECT id, nombre_taller, usuario_id FROM taller_empresa LIMIT 5')
    rows = cursor.fetchall()
    for row in rows:
        print(f"  ID: {row[0]}, Nombre: {row[1]}, Usuario ID: {row[2]}")
except Exception as e:
    print(f"Error: {e}")

# 3. Verificar usuarios
print("\n3. Usuarios existentes:")
try:
    cursor.execute('SELECT id, username FROM auth_user')
    users = cursor.fetchall()
    for user in users:
        print(f"  ID: {user[0]}, Username: {user[1]}")
except Exception as e:
    print(f"Error: {e}")

conn.close()

# 4. Verificar desde Django
print("\n4. Verificación desde Django:")
try:
    from django.contrib.auth.models import User
    from taller.models.empresa import Empresa
    
    print(f"  Total usuarios: {User.objects.count()}")
    print(f"  Total empresas: {Empresa.objects.count()}")
    
    for user in User.objects.all()[:3]:
        print(f"  Usuario: {user.username}")
        try:
            empresa = Empresa.objects.get(usuario=user)
            print(f"    ✅ Empresa: {empresa.nombre_taller}")
        except Empresa.DoesNotExist:
            print(f"    ❌ Sin empresa")
        except Exception as e:
            print(f"    ⚠️ Error: {e}")
            
except Exception as e:
    print(f"Error en verificación Django: {e}")

print("\n=== FIN DIAGNÓSTICO ===")
