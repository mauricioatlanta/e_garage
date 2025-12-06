#!/usr/bin/env python
"""
Script para crear tablas faltantes de la migración inicial
Soluciona el problema cuando algunas tablas existen pero otras no
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader


def table_exists(table_name):
    """Verifica si una tabla existe en la base de datos"""
    with connection.cursor() as cursor:
        if connection.vendor == "sqlite":
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                [table_name],
            )
        elif connection.vendor == "mysql":
            cursor.execute(
                "SHOW TABLES LIKE %s",
                [table_name],
            )
        else:
            cursor.execute(
                "SELECT tablename FROM pg_tables WHERE tablename = %s",
                [table_name],
            )
        return cursor.fetchone() is not None


def get_tables_from_migration(migration_name):
    """Obtiene las tablas que debería crear una migración"""
    loader = MigrationLoader(connection)
    migration = loader.get_migration_by_prefix("taller", migration_name)

    tables = []
    for operation in migration.operations:
        if hasattr(operation, "name"):
            # CreateModel operation
            if hasattr(operation, "name"):
                model_name = operation.name.lower()
                app_label = "taller"
                table_name = f"{app_label}_{model_name}"
                tables.append(table_name)
    return tables


def main():
    print("🔍 Verificando tablas de la migración 0001...")
    print("")

    # Tablas que debería crear la migración 0001
    expected_tables = [
        "taller_categoriaservicio",
        "taller_detalledocumento",
        "taller_documento",
        "taller_empresa",
        "taller_cliente",
        "taller_vehiculo",
        "taller_servicio",
        "taller_repuesto",
        # Agregar más según sea necesario
    ]

    missing_tables = []
    existing_tables = []

    print("📊 Estado de las tablas:")
    for table in expected_tables:
        exists = table_exists(table)
        if exists:
            existing_tables.append(table)
            print(f"  ✅ {table}")
        else:
            missing_tables.append(table)
            print(f"  ❌ {table} - FALTANTE")

    print("")

    if not missing_tables:
        print("✅ Todas las tablas existen. No hay nada que crear.")
        return 0

    print(f"⚠️  Faltan {len(missing_tables)} tablas:")
    for table in missing_tables:
        print(f"   - {table}")

    print("")
    response = input("¿Deseas crear las tablas faltantes usando sqlmigrate? (s/n): ")

    if response.lower() != "s":
        print("❌ Operación cancelada.")
        return 1

    print("")
    print("🔧 Obteniendo SQL de la migración 0001...")

    # Obtener SQL de la migración
    try:
        from io import StringIO
        from django.core.management import call_command

        output = StringIO()
        call_command("sqlmigrate", "taller", "0001_initial_migration", stdout=output)
        sql_content = output.getvalue()

        print("📝 SQL obtenido. Buscando CREATE TABLE para tablas faltantes...")
        print("")

        # Para cada tabla faltante, intentar extraer su CREATE TABLE
        for table in missing_tables:
            model_name = table.replace("taller_", "")
            print(f"🔍 Buscando CREATE TABLE para {table}...")

            # Buscar en el SQL el CREATE TABLE correspondiente
            lines = sql_content.split("\n")
            in_create = False
            create_sql = []

            for line in lines:
                if f'CREATE TABLE "{table}"' in line or f"CREATE TABLE `{table}`" in line:
                    in_create = True
                    create_sql = [line]
                elif in_create:
                    create_sql.append(line)
                    if ";" in line:
                        break

            if create_sql:
                sql_statement = "\n".join(create_sql)
                print(f"✅ SQL encontrado para {table}")
                print("")
                print("Ejecuta este SQL en dbshell:")
                print("-" * 60)
                print(sql_statement)
                print("-" * 60)
                print("")

                # Preguntar si ejecutar
                execute = input(f"¿Ejecutar este SQL para crear {table}? (s/n): ")
                if execute.lower() == "s":
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(sql_statement)
                        print(f"✅ Tabla {table} creada exitosamente")
                    except Exception as e:
                        print(f"❌ Error al crear {table}: {e}")
                        print("   Puedes ejecutarlo manualmente en dbshell")
            else:
                print(f"⚠️  No se encontró CREATE TABLE para {table}")
                print("   Necesitarás crearla manualmente o aplicar la migración completa")

        print("")
        print("📝 Siguiente paso:")
        print("   Después de crear las tablas, ejecuta:")
        print("   python manage.py migrate taller 0004 --fake")
        print("   python manage.py migrate")

    except Exception as e:
        print(f"❌ Error al obtener SQL: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())



