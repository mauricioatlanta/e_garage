#!/usr/bin/env python
"""
Script para consolidar TODOS los suscriptores de TODOS los backups
Extrae suscripciones de múltiples backups y consolida en una lista única
Ejecutar en PythonAnywhere: python tools/consolidar_suscriptores_todos_backups.py > suscripciones_consolidadas.json
"""

import os
import sys
import sqlite3
import json
from datetime import date, datetime
from collections import defaultdict

# Lista de backups a revisar (ordenados por fecha, más reciente primero)
backups = [
    '/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3',
    '/home/atlantareciclajes/apps/egarage/current/data/root_data/db.sqlite3',
    '/home/atlantareciclajes/apps/egarage/current/backups/deployments/db_backup_20251215_154133.sqlite3',
    '/home/atlantareciclajes/apps/egarage/current/backups/deployments/PROD_db_20251215_154400.sqlite3',
    '/home/atlantareciclajes/apps/egarage/db.sqlite3_SUPER_BACKUP_20251206.sqlite3',
]

# Diccionario para consolidar por email (evitar duplicados)
suscriptores_consolidados = {}
estadisticas = defaultdict(int)

print("="*80, file=sys.stderr)
print("CONSOLIDACIÓN DE SUSCRIPTORES DE TODOS LOS BACKUPS", file=sys.stderr)
print("="*80, file=sys.stderr)
print(file=sys.stderr)

for backup_path in backups:
    if not os.path.exists(backup_path):
        print(f"⚠️ Backup no encontrado: {backup_path}", file=sys.stderr)
        continue
    
    try:
        print(f"\n📂 Procesando: {backup_path}", file=sys.stderr)
        conn = sqlite3.connect(backup_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar si tiene tabla de suscripciones
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='taller_suscripcion'")
        if not cursor.fetchone():
            print(f"  ⚠️ No tiene tabla taller_suscripcion", file=sys.stderr)
            conn.close()
            continue
        
        # Obtener todas las suscripciones con datos de usuario
        query = """
        SELECT 
            s.id as suscripcion_id,
            s.user_id,
            s.tipo,
            s.fecha_inicio,
            s.fecha_fin,
            s.activa,
            u.email,
            u.username,
            u.date_joined,
            u.is_active,
            u.is_staff
        FROM taller_suscripcion s
        LEFT JOIN auth_user u ON s.user_id = u.id
        """
        
        cursor.execute(query)
        suscripciones = cursor.fetchall()
        
        print(f"  ✓ Encontradas {len(suscripciones)} suscripciones", file=sys.stderr)
        estadisticas[f'backup_{os.path.basename(backup_path)}'] = len(suscripciones)
        
        # Obtener empresas relacionadas
        for suscripcion in suscripciones:
            user_id = suscripcion['user_id']
            email = suscripcion['email'] or suscripcion['username'] or f"user_{user_id}"
            
            # Buscar empresa del usuario
            empresa_data = None
            try:
                cursor.execute("""
                    SELECT id, nombre_taller, pais, telefono, email as empresa_email
                    FROM taller_empresa
                    WHERE user_id = ? OR usuario_id = ?
                    LIMIT 1
                """, (user_id, user_id))
                empresa_row = cursor.fetchone()
                if empresa_row:
                    empresa_data = {
                        'id': empresa_row['id'],
                        'nombre_taller': empresa_row['nombre_taller'],
                        'pais': empresa_row['pais'],
                        'telefono': empresa_row['telefono'],
                        'email': empresa_row['empresa_email'],
                    }
            except Exception as e:
                pass
            
            # Crear clave única por email
            clave = email.lower().strip()
            
            # Convertir fechas a formato ISO string
            def fecha_a_iso(fecha_val):
                """Convierte fecha de SQLite a string ISO"""
                if not fecha_val:
                    return None
                if isinstance(fecha_val, str):
                    # Si ya es string, intentar parsear y convertir
                    try:
                        # Intentar diferentes formatos comunes
                        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                            try:
                                dt = datetime.strptime(fecha_val, fmt)
                                return dt.date().isoformat() if fmt == '%Y-%m-%d' else dt.isoformat()
                            except ValueError:
                                continue
                        return fecha_val  # Si no se puede parsear, devolver como está
                    except:
                        return fecha_val
                elif hasattr(fecha_val, 'isoformat'):
                    return fecha_val.isoformat()
                return str(fecha_val)
            
            fecha_inicio_iso = fecha_a_iso(suscripcion['fecha_inicio'])
            fecha_fin_iso = fecha_a_iso(suscripcion['fecha_fin'])
            date_joined_iso = fecha_a_iso(suscripcion['date_joined'])
            
            # Si ya existe, mantener la más reciente o la que tiene más datos
            if clave in suscriptores_consolidados:
                existente = suscriptores_consolidados[clave]
                # Preferir suscripción activa o más reciente
                if suscripcion['activa'] and not existente.get('activa', False):
                    # Esta es activa y la existente no, reemplazar
                    pass
                elif fecha_fin_iso and (not existente.get('fecha_fin') or fecha_fin_iso > existente.get('fecha_fin', '')):
                    # Esta tiene fecha más reciente
                    pass
                else:
                    # Mantener la existente
                    continue
            
            # Agregar o actualizar
            suscriptores_consolidados[clave] = {
                'user_email': suscripcion['email'],
                'user_username': suscripcion['username'],
                'user_id_original': user_id,
                'user_date_joined': date_joined_iso,
                'user_is_active': bool(suscripcion['is_active']),
                'user_is_staff': bool(suscripcion['is_staff']),
                'tipo': suscripcion['tipo'],
                'fecha_inicio': fecha_inicio_iso,
                'fecha_fin': fecha_fin_iso,
                'activa': bool(suscripcion['activa']),
                'empresa': empresa_data,
                'backup_origen': os.path.basename(backup_path),
            }
        
        conn.close()
        
    except Exception as e:
        print(f"  ✗ ERROR procesando {backup_path}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

# Convertir a lista
suscriptores_lista = list(suscriptores_consolidados.values())

# Agrupar por país para estadísticas
por_pais = defaultdict(int)
for suscripcion in suscriptores_lista:
    pais = suscripcion.get('empresa', {}).get('pais', 'SIN_PAIS') if suscripcion.get('empresa') else 'SIN_PAIS'
    por_pais[pais] += 1

# Generar resultado final
resultado = {
    'total_suscriptores_unicos': len(suscriptores_lista),
    'fecha_consolidacion': date.today().isoformat(),
    'estadisticas_backups': dict(estadisticas),
    'por_pais': dict(por_pais),
    'suscripciones': suscriptores_lista
}

# Mostrar resumen en stderr
print("\n" + "="*80, file=sys.stderr)
print("RESUMEN DE CONSOLIDACIÓN", file=sys.stderr)
print("="*80, file=sys.stderr)
print(f"Total suscriptores únicos: {len(suscriptores_lista)}", file=sys.stderr)
print(f"\nPor país:", file=sys.stderr)
for pais, count in sorted(por_pais.items(), key=lambda x: x[1], reverse=True):
    print(f"  {pais}: {count} suscriptores", file=sys.stderr)
print(f"\nEstadísticas por backup:", file=sys.stderr)
for backup, count in estadisticas.items():
    print(f"  {backup}: {count} suscripciones", file=sys.stderr)

# Imprimir JSON en stdout
print(json.dumps(resultado, indent=2, ensure_ascii=False))
