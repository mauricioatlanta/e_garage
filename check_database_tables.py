#!/usr/bin/env python
"""
Script para verificar qué tablas existen en la base de datos
"""
import os
import sys
import django
import sqlite3

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.conf import settings

def check_database_tables():
    """Verificar qué tablas existen en la base de datos"""
    db_path = settings.DATABASES['default']['NAME']
    print(f"🔍 Verificando base de datos: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener lista de todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📊 Total de tablas encontradas: {len(tables)}")
        
        # Buscar tablas específicas que están causando problemas
        problem_tables = [
            'taller_detalledocumento',
            'taller_suscripcion', 
            'taller_tallerinfo'
        ]
        
        print("\n🔍 Verificando tablas problemáticas:")
        for table in problem_tables:
            if table in tables:
                print(f"✅ {table} - EXISTE")
                
                # Obtener esquema de la tabla
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                print(f"   📋 Columnas ({len(columns)}):")
                for col in columns[:5]:  # Solo mostrar las primeras 5 columnas
                    print(f"      - {col[1]} ({col[2]})")
                if len(columns) > 5:
                    print(f"      ... y {len(columns) - 5} más")
            else:
                print(f"❌ {table} - NO EXISTE")
        
        # Mostrar algunas tablas relacionadas con taller
        print("\n📋 Otras tablas de taller encontradas:")
        taller_tables = [t for t in tables if t.startswith('taller_')]
        for table in sorted(taller_tables)[:10]:  # Mostrar solo las primeras 10
            print(f"   - {table}")
        if len(taller_tables) > 10:
            print(f"   ... y {len(taller_tables) - 10} más")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("VERIFICACIÓN DE TABLAS EN BASE DE DATOS")
    print("=" * 60)
    
    success = check_database_tables()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ VERIFICACIÓN COMPLETADA")
    else:
        print("❌ ERROR EN VERIFICACIÓN")
    print("=" * 60)
