#!/usr/bin/env python
"""
Script para obtener las credenciales de la base de datos desde la configuración de Django.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path("/home/atlantareciclajes/apps/egarage/current")
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Intentar leer la configuración de Django sin inicializar completamente
try:
    from django.conf import settings

    # Leer configuración de base de datos
    db_config = settings.DATABASES.get("default", {})

    print("=" * 80)
    print("📋 CONFIGURACIÓN DE BASE DE DATOS ENCONTRADA")
    print("=" * 80)
    print(f"Engine: {db_config.get('ENGINE', 'N/A')}")
    print(f"Name: {db_config.get('NAME', 'N/A')}")
    print(f"User: {db_config.get('USER', 'N/A')}")
    print(f"Host: {db_config.get('HOST', 'N/A')}")
    print(f"Port: {db_config.get('PORT', 'N/A')}")
    print(
        f"Password: {'*' * len(db_config.get('PASSWORD', '')) if db_config.get('PASSWORD') else 'VACÍA'}"
    )
    print()

    # Ahora intentar conectar
    import pymysql

    DB_HOST = db_config.get("HOST", "localhost")
    DB_NAME = db_config.get("NAME", "").replace("$", "")
    DB_USER = db_config.get("USER", "root")
    DB_PASSWORD = db_config.get("PASSWORD", "")
    DB_PORT = int(db_config.get("PORT", 3306))

    print("🔌 Intentando conectar...")
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
    )

    print("✅ ¡Conexión exitosa!")

    # Consultar datos
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM taller_empresa WHERE suscripcion_activa = 1")
        total_empresas = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM taller_suscripcion WHERE activa = 1")
        total_suscripciones = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM taller_trialregistro WHERE prueba_activa = 1")
        total_trials = cursor.fetchone()["total"]

        print("\n" + "=" * 80)
        print("📊 ESTADÍSTICAS GENERALES")
        print("=" * 80)
        print(f"Total Empresas Activas: {total_empresas}")
        print(f"Total Suscripciones Activas: {total_suscripciones}")
        print(f"Total Trials Activos: {total_trials}")
        print()

        cursor.execute(
            """
            SELECT pais, COUNT(*) as total,
                   SUM(CASE WHEN plan = 'trial' THEN 1 ELSE 0 END) as trials,
                   SUM(CASE WHEN plan != 'trial' THEN 1 ELSE 0 END) as pagadas
            FROM taller_empresa
            WHERE suscripcion_activa = 1
            GROUP BY pais
            ORDER BY pais
        """
        )
        paises = cursor.fetchall()

        print("=" * 80)
        print("🌍 RESUMEN POR PAÍS")
        print("=" * 80)
        for row in paises:
            paises_nombres = {"CL": "Chile", "US": "Estados Unidos", "MX": "México"}
            pais_nombre = paises_nombres.get(row["pais"], row["pais"])
            print(f"\n{pais_nombre} ({row['pais']}):")
            print(f"  Total Empresas: {row['total']}")
            print(f"  - Trials: {row['trials']}")
            print(f"  - Pagadas: {row['pagadas']}")

        # Detalle por país
        for row in paises:
            pais_codigo = row["pais"]
            paises_nombres = {"CL": "Chile", "US": "Estados Unidos", "MX": "México"}
            pais_nombre = paises_nombres.get(pais_codigo, pais_codigo)

            print("\n" + "=" * 80)
            print(f"🌍 PAÍS: {pais_nombre} ({pais_codigo})")
            print("=" * 80)

            cursor.execute(
                """
                SELECT e.nombre_taller, e.plan, u.username, u.email, 
                       e.fecha_inicio, e.fecha_fin, e.direccion, e.telefono
                FROM taller_empresa e
                LEFT JOIN auth_user u ON e.user_id = u.id
                WHERE e.pais = %s AND e.suscripcion_activa = 1
                ORDER BY e.nombre_taller
            """,
                (pais_codigo,),
            )

            empresas = cursor.fetchall()

            print(f"\n🏢 EMPRESAS ACTIVAS: {len(empresas)}")
            print("-" * 80)

            for idx, emp in enumerate(empresas, 1):
                es_trial = "TRIAL" if emp["plan"] == "trial" else (emp["plan"] or "N/A").upper()
                print(f"\n  {idx}. ✅ {emp['nombre_taller']}")
                print(f"     Usuario: {emp['username']}")
                print(f"     Email: {emp['email']}")
                print(f"     Plan: {es_trial}")
                print(f"     Fecha Inicio: {emp['fecha_inicio']}")
                print(f"     Fecha Fin: {emp['fecha_fin']}")
                if emp["direccion"]:
                    print(f"     Dirección: {emp['direccion']}")
                if emp["telefono"]:
                    print(f"     Teléfono: {emp['telefono']}")

        # Trials activos
        cursor.execute(
            """
            SELECT t.nombre, t.email, t.telefono, t.fecha_registro, t.fecha_activacion, e.pais
            FROM taller_trialregistro t
            LEFT JOIN taller_empresa e ON t.email = e.email
            WHERE t.prueba_activa = 1
            ORDER BY t.fecha_registro
        """
        )

        trials = cursor.fetchall()

        print("\n" + "=" * 80)
        print("🧪 TODAS LAS CUENTAS DE PRUEBA ACTIVAS (TRIALS)")
        print("=" * 80)
        if trials:
            for idx, trial in enumerate(trials, 1):
                paises_nombres = {"CL": "Chile", "US": "Estados Unidos", "MX": "México"}
                pais_nombre = paises_nombres.get(trial["pais"], trial["pais"] or "N/A")
                print(f"\n  {idx}. {trial['nombre']} ({pais_nombre})")
                print(f"     Email: {trial['email']}")
                print(f"     Teléfono: {trial['telefono']}")
                print(f"     Fecha Registro: {trial['fecha_registro']}")
                print(f"     Fecha Activación: {trial['fecha_activacion']}")
        else:
            print("  ⚠️  No hay trials activos")

    connection.close()
    print("\n" + "=" * 80)
    print("✅ Reporte completado")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
