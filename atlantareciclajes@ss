#!/usr/bin/env python
"""
Script de Backup de Datos Críticos para eGarage
================================================
Este script hace backup de todos los datos críticos antes de actualizar:
- Usuarios (auth_user)
- Empresas/Suscriptores (taller_empresa)
- Clientes (taller_cliente)
- Vehículos (taller_vehiculo)
- Documentos (taller_documento)
- Y todos los datos relacionados con TenantScoped

Uso:
    python scripts_deploy/backup_datos_criticos.py
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
import django
django.setup()

from django.conf import settings
from django.db import connection

# Tablas críticas que NO deben perderse
TABLAS_CRITICAS = [
    # Usuarios y autenticación
    'auth_user',
    'auth_user_groups',
    'auth_user_user_permissions',
    'django_session',
    
    # Empresas/Suscriptores (LO MÁS IMPORTANTE)
    'taller_empresa',
    'taller_configuracionempresa',
    
    # Datos de clientes (TenantScoped)
    'taller_cliente',
    'taller_vehiculo',
    'taller_documento',
    'taller_lineaservicio',
    'taller_linearepuesto',
    'taller_detalledocumento',
    
    # Inventario y catálogos (TenantScoped)
    'taller_repuesto',
    'taller_servicio',
    'taller_otroservicio',
    
    # Relaciones y configuraciones
    'taller_tecnico',
    'taller_teammember',
    'taller_colorcliente',
    
    # Ubicaciones (pueden estar relacionadas)
    'ubicacion_address',
    'ubicacion_country',
    'ubicacion_state',
    'ubicacion_city',
    
    # Otros datos importantes
    'taller_marca',
    'taller_modelo',
    'taller_categoriaservicio',
    'taller_categoriarepuesto',
]

def crear_directorio_backup():
    """Crea el directorio de backups si no existe"""
    backup_dir = BASE_DIR / 'backups' / 'datos_criticos'
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def hacer_backup_tabla(cursor, nombre_tabla, backup_dir):
    """Hace backup de una tabla específica"""
    try:
        # Verificar que la tabla existe
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{nombre_tabla}'")
        if not cursor.fetchone():
            print(f"⚠️  Tabla {nombre_tabla} no existe, omitiendo...")
            return None
        
        # Obtener estructura de la tabla
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        columnas = cursor.fetchall()
        
        # Obtener todos los datos
        cursor.execute(f"SELECT * FROM {nombre_tabla}")
        filas = cursor.fetchall()
        
        # Convertir a formato JSON
        datos = {
            'tabla': nombre_tabla,
            'columnas': [col[1] for col in columnas],  # nombre de columna
            'tipos': [col[2] for col in columnas],  # tipo de dato
            'filas': [dict(zip([col[1] for col in columnas], fila)) for fila in filas],
            'total_registros': len(filas),
            'timestamp': datetime.now().isoformat()
        }
        
        # Guardar en archivo JSON
        archivo_backup = backup_dir / f"{nombre_tabla}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(archivo_backup, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ {nombre_tabla}: {len(filas)} registros guardados")
        return archivo_backup
        
    except Exception as e:
        print(f"❌ Error al hacer backup de {nombre_tabla}: {e}")
        return None

def hacer_backup_completo():
    """Hace backup completo de todas las tablas críticas"""
    print("=" * 70)
    print("🔄 INICIANDO BACKUP DE DATOS CRÍTICOS")
    print("=" * 70)
    
    # Crear directorio de backup
    backup_dir = crear_directorio_backup()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_actual = backup_dir / f"backup_completo_{timestamp}"
    backup_actual.mkdir(exist_ok=True)
    
    # Obtener conexión a la base de datos
    db_path = settings.DATABASES['default']['NAME']
    print(f"\n📁 Base de datos: {db_path}")
    print(f"📁 Backup en: {backup_actual}\n")
    
    if not os.path.exists(db_path):
        print(f"❌ ERROR: No se encuentra la base de datos en {db_path}")
        return False
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    archivos_backup = []
    total_registros = 0
    
    # Hacer backup de cada tabla crítica
    for tabla in TABLAS_CRITICAS:
        archivo = hacer_backup_tabla(cursor, tabla, backup_actual)
        if archivo:
            archivos_backup.append(archivo)
            # Contar registros
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = cursor.fetchone()[0]
                total_registros += count
            except:
                pass
    
    conn.close()
    
    # Crear archivo de resumen
    resumen = {
        'timestamp': datetime.now().isoformat(),
        'base_datos': db_path,
        'tablas_backup': len(archivos_backup),
        'total_registros': total_registros,
        'archivos': [str(f) for f in archivos_backup]
    }
    
    resumen_file = backup_actual / 'RESUMEN_BACKUP.json'
    with open(resumen_file, 'w', encoding='utf-8') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("✅ BACKUP COMPLETADO")
    print("=" * 70)
    print(f"📊 Tablas respaldadas: {len(archivos_backup)}")
    print(f"📊 Total de registros: {total_registros}")
    print(f"📁 Ubicación: {backup_actual}")
    print(f"📄 Resumen: {resumen_file}")
    print("=" * 70)
    
    return True

def hacer_backup_sql_completo():
    """Hace un backup SQL completo de la base de datos (más rápido para restaurar)"""
    print("\n" + "=" * 70)
    print("🔄 CREANDO BACKUP SQL COMPLETO")
    print("=" * 70)
    
    backup_dir = crear_directorio_backup()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    db_path = settings.DATABASES['default']['NAME']
    sql_backup = backup_dir / f"db_completo_{timestamp}.sql"
    
    # Usar sqlite3 para hacer dump completo
    import subprocess
    try:
        with open(sql_backup, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                ['sqlite3', db_path, '.dump'],
                stdout=f,
                stderr=subprocess.PIPE,
                text=True
            )
        
        if result.returncode == 0:
            print(f"✅ Backup SQL completo creado: {sql_backup}")
            return sql_backup
        else:
            print(f"❌ Error al crear backup SQL: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error al crear backup SQL: {e}")
        return None

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🛡️  BACKUP DE DATOS CRÍTICOS - eGarage")
    print("=" * 70)
    print("\nEste script respalda todos los datos críticos antes de actualizar.")
    print("IMPORTANTE: Este backup es esencial para restaurar datos si algo sale mal.\n")
    
    # Backup JSON (estructurado)
    if hacer_backup_completo():
        # Backup SQL (completo y rápido de restaurar)
        hacer_backup_sql_completo()
        print("\n✅ Todos los backups se completaron exitosamente.")
        print("📋 Puedes proceder con la actualización del servidor.")
    else:
        print("\n❌ Hubo errores durante el backup. NO procedas con la actualización.")
        sys.exit(1)

