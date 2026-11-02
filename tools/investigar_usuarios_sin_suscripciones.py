#!/usr/bin/env python
"""
Script para investigar usuarios que tienen empresas pero no suscripciones
Esto puede indicar que las suscripciones se perdieron o están en otro formato
"""

import os
import sqlite3
from datetime import datetime

# Backup principal para investigar
backup_principal = '/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3'

print("="*80)
print("INVESTIGACIÓN: USUARIOS CON EMPRESAS PERO SIN SUSCRIPCIONES")
print("="*80)
print()

try:
    conn = sqlite3.connect(backup_principal)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Obtener todos los usuarios con empresas
    cursor.execute("""
        SELECT DISTINCT
            u.id as user_id,
            u.email,
            u.username,
            u.date_joined,
            u.is_active,
            e.id as empresa_id,
            e.nombre_taller,
            e.pais,
            e.user_id as empresa_user_id,
            e.usuario_id as empresa_usuario_id
        FROM auth_user u
        LEFT JOIN taller_empresa e ON (e.user_id = u.id OR e.usuario_id = u.id)
        WHERE e.id IS NOT NULL
        ORDER BY u.date_joined
    """)
    
    usuarios_con_empresas = cursor.fetchall()
    
    # Obtener todas las suscripciones
    cursor.execute("""
        SELECT user_id, tipo, activa, fecha_fin
        FROM taller_suscripcion
    """)
    
    suscripciones_existentes = {row['user_id']: row for row in cursor.fetchall()}
    
    print(f"Total usuarios con empresas: {len(usuarios_con_empresas)}")
    print(f"Total suscripciones registradas: {len(suscripciones_existentes)}")
    print()
    
    usuarios_sin_suscripcion = []
    usuarios_con_suscripcion = []
    
    for row in usuarios_con_empresas:
        user_id = row['user_id']
        tiene_suscripcion = user_id in suscripciones_existentes
        
        if tiene_suscripcion:
            usuarios_con_suscripcion.append(row)
        else:
            usuarios_sin_suscripcion.append(row)
    
    print("="*80)
    print("USUARIOS CON EMPRESAS Y SIN SUSCRIPCIÓN")
    print("="*80)
    print(f"Total: {len(usuarios_sin_suscripcion)}")
    print()
    
    for row in usuarios_sin_suscripcion:
        print(f"  - {row['email'] or row['username']} (ID: {row['user_id']})")
        print(f"    Empresa: {row['nombre_taller']} | País: {row['pais']}")
        print(f"    Fecha registro: {row['date_joined']}")
        print()
    
    print("="*80)
    print("USUARIOS CON EMPRESAS Y CON SUSCRIPCIÓN")
    print("="*80)
    print(f"Total: {len(usuarios_con_suscripcion)}")
    print()
    
    for row in usuarios_con_suscripcion:
        suscripcion = suscripciones_existentes[row['user_id']]
        print(f"  - {row['email'] or row['username']} (ID: {row['user_id']})")
        print(f"    Empresa: {row['nombre_taller']} | País: {row['pais']}")
        print(f"    Suscripción: {suscripcion['tipo']} | Activa: {suscripcion['activa']} | Fin: {suscripcion['fecha_fin']}")
        print()
    
    # Verificar si hay otras tablas relacionadas con suscripciones
    print("="*80)
    print("TABLAS RELACIONADAS CON SUSCRIPCIONES")
    print("="*80)
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND (name LIKE '%suscrip%' OR name LIKE '%subscription%' OR name LIKE '%trial%')
        ORDER BY name
    """)
    
    tablas_relacionadas = cursor.fetchall()
    for tabla in tablas_relacionadas:
        nombre_tabla = tabla['name']
        cursor.execute(f"SELECT COUNT(*) as total FROM {nombre_tabla}")
        total = cursor.fetchone()['total']
        print(f"  - {nombre_tabla}: {total} registros")
        
        # Si tiene registros, mostrar algunos ejemplos
        if total > 0 and total < 20:
            cursor.execute(f"SELECT * FROM {nombre_tabla} LIMIT 3")
            ejemplos = cursor.fetchall()
            for ejemplo in ejemplos:
                print(f"    Ejemplo: {dict(ejemplo)}")
    
    # Verificar empresas por país
    print()
    print("="*80)
    print("EMPRESAS POR PAÍS")
    print("="*80)
    
    cursor.execute("""
        SELECT pais, COUNT(*) as total
        FROM taller_empresa
        GROUP BY pais
        ORDER BY total DESC
    """)
    
    empresas_por_pais = cursor.fetchall()
    for row in empresas_por_pais:
        print(f"  {row['pais']}: {row['total']} empresas")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
