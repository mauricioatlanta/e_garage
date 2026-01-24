#!/usr/bin/env python
"""
Script para buscar TODOS los backups de SQLite en PythonAnywhere
y mostrar cuántos suscriptores tiene cada uno
"""

import os
import sqlite3
from datetime import datetime

# Directorios base para buscar
directorios_buscar = [
    '/home/atlantareciclajes',
    '/home/atlantareciclajes/apps',
    '/home/atlantareciclajes/apps/egarage',
    '/home/atlantareciclajes/respaldo_atlanta',
]

print("="*80)
print("BÚSQUEDA AUTOMÁTICA DE BACKUPS")
print("="*80)
print()

backups_encontrados = []

# Buscar todos los archivos .sqlite3, .db, .sql
for directorio_base in directorios_buscar:
    if not os.path.exists(directorio_base):
        continue
    
    print(f"Buscando en: {directorio_base}")
    for root, dirs, files in os.walk(directorio_base):
        # Saltar directorios muy grandes o innecesarios
        if 'node_modules' in root or '.git' in root:
            continue
        
        for file in files:
            if file.endswith(('.sqlite3', '.db')) and 'sqlite' in file.lower():
                ruta_completa = os.path.join(root, file)
                try:
                    # Verificar que es un archivo SQLite válido
                    conn = sqlite3.connect(ruta_completa)
                    cursor = conn.cursor()
                    
                    # Verificar si tiene tabla de suscripciones
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='taller_suscripcion'")
                    tiene_suscripciones = cursor.fetchone()
                    
                    suscripciones = 0
                    usuarios = 0
                    empresas = 0
                    
                    if tiene_suscripciones:
                        cursor.execute("SELECT COUNT(*) FROM taller_suscripcion")
                        suscripciones = cursor.fetchone()[0]
                    
                    # Verificar usuarios
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auth_user'")
                    if cursor.fetchone():
                        cursor.execute("SELECT COUNT(*) FROM auth_user")
                        usuarios = cursor.fetchone()[0]
                    
                    # Verificar empresas
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='taller_empresa'")
                    if cursor.fetchone():
                        cursor.execute("SELECT COUNT(*) FROM taller_empresa")
                        empresas = cursor.fetchone()[0]
                    
                    conn.close()
                    
                    # Obtener tamaño y fecha de modificación
                    tamaño = os.path.getsize(ruta_completa)
                    fecha_mod = datetime.fromtimestamp(os.path.getmtime(ruta_completa))
                    
                    backups_encontrados.append({
                        'ruta': ruta_completa,
                        'tamaño': tamaño,
                        'fecha_mod': fecha_mod,
                        'suscripciones': suscripciones,
                        'usuarios': usuarios,
                        'empresas': empresas,
                    })
                    
                except Exception as e:
                    # No es un SQLite válido o hay error
                    pass

# Ordenar por número de suscripciones (mayor primero)
backups_encontrados.sort(key=lambda x: x['suscripciones'], reverse=True)

print()
print("="*80)
print("BACKUPS ENCONTRADOS (ordenados por número de suscripciones)")
print("="*80)
print()

if not backups_encontrados:
    print("No se encontraron backups de SQLite")
else:
    for backup in backups_encontrados:
        print(f"📂 {backup['ruta']}")
        print(f"   Tamaño: {backup['tamaño'] / (1024*1024):.2f} MB")
        print(f"   Modificado: {backup['fecha_mod'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Suscripciones: {backup['suscripciones']}")
        print(f"   Usuarios: {backup['usuarios']}")
        print(f"   Empresas: {backup['empresas']}")
        print()

# Mostrar el backup con más suscripciones
if backups_encontrados:
    mejor_backup = backups_encontrados[0]
    print("="*80)
    print("BACKUP CON MÁS SUSCRIPCIONES")
    print("="*80)
    print(f"Ruta: {mejor_backup['ruta']}")
    print(f"Suscripciones: {mejor_backup['suscripciones']}")
    print(f"Usuarios: {mejor_backup['usuarios']}")
    print(f"Empresas: {mejor_backup['empresas']}")
    print()
    print("Este backup debería ser el que uses para la consolidación.")
    
    # Mostrar detalles de las suscripciones del mejor backup
    if mejor_backup['suscripciones'] > 0:
        print()
        print("Detalles de suscripciones (primeras 10):")
        try:
            conn = sqlite3.connect(mejor_backup['ruta'])
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT s.id, s.user_id, s.tipo, s.activa, s.fecha_fin,
                       u.email, u.username
                FROM taller_suscripcion s
                LEFT JOIN auth_user u ON s.user_id = u.id
                LIMIT 10
            """)
            
            for row in cursor.fetchall():
                print(f"  - ID: {row['id']} | User: {row['email'] or row['username']} | Tipo: {row['tipo']} | Activa: {row['activa']} | Fin: {row['fecha_fin']}")
            
            conn.close()
        except Exception as e:
            print(f"  Error al leer detalles: {e}")

print()
print("="*80)
print("RECOMENDACIÓN")
print("="*80)
print("Actualiza el script consolidar_suscriptores_todos_backups.py con TODOS")
print("los backups encontrados arriba para asegurar que no se pierda ningún dato.")
