#!/usr/bin/env python
"""
Script para consolidar suscriptores del backup real y crear suscripciones
para usuarios que tienen empresas pero no tienen suscripción registrada
"""

import os
import sys
import sqlite3
import json
from datetime import date, datetime, timedelta
from collections import defaultdict

# Backup principal (el real)
backup_principal = '/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3'

print("="*80, file=sys.stderr)
print("CONSOLIDACIÓN DEL BACKUP REAL Y CREACIÓN DE SUSCRIPCIONES FALTANTES", file=sys.stderr)
print("="*80, file=sys.stderr)
print(file=sys.stderr)

suscriptores_consolidados = {}

try:
    conn = sqlite3.connect(backup_principal)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Verificar columnas de taller_empresa
    cursor.execute("PRAGMA table_info(taller_empresa)")
    columnas_empresa = [row[1] for row in cursor.fetchall()]
    tiene_user_id = 'user_id' in columnas_empresa
    
    # Obtener todas las suscripciones existentes
    cursor.execute("""
        SELECT s.id, s.user_id, s.tipo, s.fecha_inicio, s.fecha_fin, s.activa,
               u.email, u.username, u.date_joined, u.is_active, u.is_staff
        FROM taller_suscripcion s
        LEFT JOIN auth_user u ON s.user_id = u.id
    """)
    
    suscripciones_existentes = cursor.fetchall()
    print(f"✓ Encontradas {len(suscripciones_existentes)} suscripciones existentes", file=sys.stderr)
    
    # Procesar suscripciones existentes
    for suscripcion in suscripciones_existentes:
        email = suscripcion['email'] or suscripcion['username'] or f"user_{suscripcion['user_id']}"
        clave = email.lower().strip()
        
        # Buscar empresa del usuario
        empresa_data = None
        if tiene_user_id:
            cursor.execute("""
                SELECT id, nombre_taller, pais, telefono, email as empresa_email
                FROM taller_empresa
                WHERE user_id = ?
                LIMIT 1
            """, (suscripcion['user_id'],))
        else:
            cursor.execute("""
                SELECT id, nombre_taller, pais, telefono, email as empresa_email
                FROM taller_empresa
                WHERE usuario_id = ?
                LIMIT 1
            """, (suscripcion['user_id'],))
        
        empresa_row = cursor.fetchone()
        if empresa_row:
            empresa_data = {
                'id': empresa_row['id'],
                'nombre_taller': empresa_row['nombre_taller'],
                'pais': empresa_row['pais'],
                'telefono': empresa_row['telefono'],
                'email': empresa_row['empresa_email'],
            }
        
        # Convertir fechas
        def fecha_a_iso(fecha_val):
            if not fecha_val:
                return None
            if isinstance(fecha_val, str):
                try:
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                        try:
                            dt = datetime.strptime(fecha_val, fmt)
                            return dt.date().isoformat() if fmt == '%Y-%m-%d' else dt.isoformat()
                        except ValueError:
                            continue
                    return fecha_val
                except:
                    return fecha_val
            elif hasattr(fecha_val, 'isoformat'):
                return fecha_val.isoformat()
            return str(fecha_val)
        
        suscriptores_consolidados[clave] = {
            'user_email': suscripcion['email'],
            'user_username': suscripcion['username'],
            'user_id_original': suscripcion['user_id'],
            'user_date_joined': fecha_a_iso(suscripcion['date_joined']),
            'user_is_active': bool(suscripcion['is_active']),
            'user_is_staff': bool(suscripcion['is_staff']),
            'tipo': suscripcion['tipo'],
            'fecha_inicio': fecha_a_iso(suscripcion['fecha_inicio']),
            'fecha_fin': fecha_a_iso(suscripcion['fecha_fin']),
            'activa': bool(suscripcion['activa']),
            'empresa': empresa_data,
            'backup_origen': 'shared_db.sqlite3',
            'tiene_suscripcion_original': True,
        }
    
    # Obtener usuarios con empresas pero sin suscripciones
    if tiene_user_id:
        cursor.execute("""
            SELECT DISTINCT u.id, u.email, u.username, u.date_joined, u.is_active, u.is_staff,
                   e.id as empresa_id, e.nombre_taller, e.pais, e.telefono, e.email as empresa_email
            FROM auth_user u
            INNER JOIN taller_empresa e ON e.user_id = u.id
            WHERE u.id NOT IN (SELECT user_id FROM taller_suscripcion)
            ORDER BY u.date_joined
        """)
    else:
        cursor.execute("""
            SELECT DISTINCT u.id, u.email, u.username, u.date_joined, u.is_active, u.is_staff,
                   e.id as empresa_id, e.nombre_taller, e.pais, e.telefono, e.email as empresa_email
            FROM auth_user u
            INNER JOIN taller_empresa e ON e.usuario_id = u.id
            WHERE u.id NOT IN (SELECT user_id FROM taller_suscripcion)
            ORDER BY u.date_joined
        """)
    
    usuarios_sin_suscripcion = cursor.fetchall()
    print(f"✓ Encontrados {len(usuarios_sin_suscripcion)} usuarios con empresas pero sin suscripción", file=sys.stderr)
    
    # Crear suscripciones para estos usuarios
    for usuario in usuarios_sin_suscripcion:
        email = usuario['email'] or usuario['username'] or f"user_{usuario['id']}"
        clave = email.lower().strip()
        
        # Si ya existe (por alguna razón), saltar
        if clave in suscriptores_consolidados:
            continue
        
        # Crear suscripción trial de 30 días desde la fecha de registro
        fecha_registro = usuario['date_joined']
        if isinstance(fecha_registro, str):
            try:
                fecha_registro = datetime.fromisoformat(fecha_registro.replace('Z', '+00:00'))
            except:
                fecha_registro = datetime.now()
        elif not fecha_registro:
            fecha_registro = datetime.now()
        
        if isinstance(fecha_registro, datetime):
            fecha_inicio = fecha_registro.date()
        else:
            fecha_inicio = date.today()
        
        fecha_fin = fecha_inicio + timedelta(days=30)
        
        empresa_data = {
            'id': usuario['empresa_id'],
            'nombre_taller': usuario['nombre_taller'],
            'pais': usuario['pais'],
            'telefono': usuario['telefono'],
            'email': usuario['empresa_email'],
        }
        
        suscriptores_consolidados[clave] = {
            'user_email': usuario['email'],
            'user_username': usuario['username'],
            'user_id_original': usuario['id'],
            'user_date_joined': fecha_a_iso(usuario['date_joined']),
            'user_is_active': bool(usuario['is_active']),
            'user_is_staff': bool(usuario['is_staff']),
            'tipo': 'trial',
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'activa': True,  # Asumir activa si tienen empresa
            'empresa': empresa_data,
            'backup_origen': 'shared_db.sqlite3',
            'tiene_suscripcion_original': False,  # Creada automáticamente
        }
        
        print(f"  ✓ Creada suscripción para: {email} | {usuario['nombre_taller']} | {usuario['pais']}", file=sys.stderr)
    
    conn.close()
    
except Exception as e:
    print(f"✗ ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

# Convertir a lista
suscriptores_lista = list(suscriptores_consolidados.values())

# Agrupar por país
por_pais = defaultdict(int)
for suscripcion in suscriptores_lista:
    pais = suscripcion.get('empresa', {}).get('pais', 'SIN_PAIS') if suscripcion.get('empresa') else 'SIN_PAIS'
    por_pais[pais] += 1

# Estadísticas
suscripciones_originales = sum(1 for s in suscriptores_lista if s.get('tiene_suscripcion_original', False))
suscripciones_creadas = sum(1 for s in suscriptores_lista if not s.get('tiene_suscripcion_original', True))

# Generar resultado
resultado = {
    'total_suscriptores_unicos': len(suscriptores_lista),
    'fecha_consolidacion': date.today().isoformat(),
    'suscripciones_originales': suscripciones_originales,
    'suscripciones_creadas_automaticamente': suscripciones_creadas,
    'por_pais': dict(por_pais),
    'suscripciones': suscriptores_lista
}

# Mostrar resumen en stderr
print("\n" + "="*80, file=sys.stderr)
print("RESUMEN DE CONSOLIDACIÓN", file=sys.stderr)
print("="*80, file=sys.stderr)
print(f"Total suscriptores únicos: {len(suscriptores_lista)}", file=sys.stderr)
print(f"  - Suscripciones originales: {suscripciones_originales}", file=sys.stderr)
print(f"  - Suscripciones creadas automáticamente: {suscripciones_creadas}", file=sys.stderr)
print(f"\nPor país:", file=sys.stderr)
for pais, count in sorted(por_pais.items(), key=lambda x: x[1], reverse=True):
    print(f"  {pais}: {count} suscriptores", file=sys.stderr)

# Imprimir JSON en stdout
print(json.dumps(resultado, indent=2, ensure_ascii=False))
