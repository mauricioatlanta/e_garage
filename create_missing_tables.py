#!/usr/bin/env python
"""
Script para crear las tablas faltantes manualmente
"""
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.core.management.color import no_style
from django.db import connection, models


def create_missing_tables():
    """Crear las tablas faltantes manualmente"""
    print("🔧 Creando tablas faltantes...")

    try:
        # Importar los modelos
        from taller.models.suscripcion import Suscripcion
        from taller.models.taller_info import TallerInfo

        # Obtener el esquema editor de Django
        with connection.schema_editor() as schema_editor:
            # Verificar si las tablas existen antes de crearlas
            table_names = connection.introspection.table_names()

            # Crear tabla Suscripcion si no existe
            if "taller_suscripcion" not in table_names:
                print("📋 Creando tabla taller_suscripcion...")
                schema_editor.create_model(Suscripcion)
                print("✅ Tabla taller_suscripcion creada")
            else:
                print("ℹ️ Tabla taller_suscripcion ya existe")

            # Crear tabla TallerInfo si no existe
            if "taller_tallerinfo" not in table_names:
                print("📋 Creando tabla taller_tallerinfo...")
                schema_editor.create_model(TallerInfo)
                print("✅ Tabla taller_tallerinfo creada")
            else:
                print("ℹ️ Tabla taller_tallerinfo ya existe")

        return True

    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_tables():
    """Verificar que todas las tablas necesarias existen"""
    print("\n🔍 Verificando tablas...")

    try:
        table_names = connection.introspection.table_names()
        required_tables = [
            "taller_detalledocumento",
            "taller_suscripcion",
            "taller_tallerinfo",
        ]

        all_exist = True
        for table in required_tables:
            if table in table_names:
                print(f"✅ {table} - EXISTE")
            else:
                print(f"❌ {table} - NO EXISTE")
                all_exist = False

        return all_exist

    except Exception as e:
        print(f"❌ Error al verificar tablas: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CREACIÓN DE TABLAS FALTANTES")
    print("=" * 60)

    # Crear tablas faltantes
    creation_success = create_missing_tables()

    # Verificar que todo esté correcto
    verification_success = verify_tables()

    print("\n" + "=" * 60)
    if creation_success and verification_success:
        print("🎉 TODAS LAS TABLAS ESTÁN LISTAS")
    else:
        print("💥 HAY PROBLEMAS CON LAS TABLAS")
    print("=" * 60)
