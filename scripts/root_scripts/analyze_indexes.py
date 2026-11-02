#!/usr/bin/env python
"""
Script para analizar el uso de índices en la base de datos
Basado en las recomendaciones de Mauricio para optimizar eGarage
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db import connection


def analyze_index_usage():
    """Analiza el uso de índices con EXPLAIN QUERY PLAN"""

    print("🔍 ANÁLISIS DE ÍNDICES - eGarage")
    print("=" * 50)

    # Consultas típicas que deberían usar los índices
    queries = [
        (
            "por_técnico_mes",
            """
         EXPLAIN QUERY PLAN
         SELECT documento_id
         FROM taller_documento
         WHERE tecnico_responsable_id=123 AND fecha_emision BETWEEN '2025-09-01' AND '2025-09-30';
         """,
        ),
        (
            "por_cliente_mes",
            """
         EXPLAIN QUERY PLAN
         SELECT id
         FROM taller_documento
         WHERE cliente_id=456 AND fecha_emision BETWEEN '2025-09-01' AND '2025-09-30';
         """,
        ),
        (
            "por_técnico_solo",
            """
         EXPLAIN QUERY PLAN
         SELECT id
         FROM taller_documento
         WHERE tecnico_responsable_id=123;
         """,
        ),
        (
            "por_cliente_solo",
            """
         EXPLAIN QUERY PLAN
         SELECT id
         FROM taller_documento
         WHERE cliente_id=456;
         """,
        ),
        (
            "por_fecha_solo",
            """
         EXPLAIN QUERY PLAN
         SELECT id
         FROM taller_documento
         WHERE fecha_emision BETWEEN '2025-09-01' AND '2025-09-30';
         """,
        ),
    ]

    for name, sql in queries:
        print(f"\n📊 {name.upper()}")
        print("-" * 30)
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                for row in results:
                    print(f"  {row[0]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n" + "=" * 50)
    print("💡 RECOMENDACIONES:")
    print("1. Si 'por_técnico_mes' usa doc_tec_fem_idx, podrías remover doc_tec_idx")
    print("2. Si 'por_cliente_mes' usa doc_cli_fem_idx, podrías remover índice solo de cliente")
    print("3. Si 'por_fecha_solo' no usa índice, considera crear uno solo para fecha")


def show_current_indexes():
    """Muestra los índices actuales en la tabla de documentos"""

    print("\n🗂️  ÍNDICES ACTUALES EN taller_documento:")
    print("-" * 40)

    try:
        with connection.cursor() as cursor:
            # Para SQLite
            cursor.execute(
                """
                SELECT name, sql
                FROM sqlite_master
                WHERE type='index' AND tbl_name='taller_documento'
                ORDER BY name;
            """
            )
            results = cursor.fetchall()

            for name, sql in results:
                if sql:  # Ignorar índices automáticos
                    print(f"  📋 {name}")
                    print(f"     {sql}")
                    print()
    except Exception as e:
        print(f"  ❌ Error obteniendo índices: {e}")


if __name__ == "__main__":
    show_current_indexes()
    analyze_index_usage()
