#!/usr/bin/env python
"""
Script para consultar suscripciones en PythonAnywhere usando PyMySQL.
Conecta directamente a la base de datos sin pasar por Django.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Configuración de base de datos para PythonAnywhere
DB_HOST = os.getenv("DB_HOST", "atlantareciclajes.mysql.pythonanywhere-services.com")
DB_NAME = os.getenv("DB_NAME", "atlantareciclajes$egarage").replace("$", "")
DB_USER = os.getenv("DB_USER", "atlantareciclajes")
DB_PASSWORD = os.getenv("DB_PASSWORD", "laila2013")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

try:
    import pymysql

    def obtener_nombre_pais(codigo):
        paises = {
            "CL": "Chile",
            "US": "Estados Unidos",
            "MX": "México",
            "PE": "Perú",
            "CO": "Colombia",
            "EC": "Ecuador",
            "BR": "Brasil",
            "VE": "Venezuela",
        }
        return paises.get(codigo, codigo)

    def formatear_fecha(fecha):
        if not fecha:
            return "N/A"
        if isinstance(fecha, str):
            return fecha
        try:
            return fecha.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return str(fecha)

    print("=" * 80)
    print("📊 REPORTE DE SUSCRIPCIONES ACTIVAS")
    print("=" * 80)
    print()

    # Conectar a la base de datos
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
    )

    with connection.cursor() as cursor:
        # Estadísticas generales
        cursor.execute("SELECT COUNT(*) as total FROM taller_empresa WHERE suscripcion_activa = 1")
        total_empresas = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM taller_suscripcion WHERE activa = 1")
        total_suscripciones = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM taller_trialregistro WHERE prueba_activa = 1")
        total_trials = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) as total FROM auth_user WHERE is_active = 1 AND is_staff = 0 AND is_superuser = 0"
        )
        total_usuarios = cursor.fetchone()["total"]

        print("📈 ESTADÍSTICAS GENERALES")
        print("-" * 80)
        print(f"Total Empresas con Suscripción Activa: {total_empresas}")
        print(f"Total Suscripciones Activas (modelo Suscripcion): {total_suscripciones}")
        print(f"Total Trials Activos: {total_trials}")
        print(f"Total Usuarios Registrados (no staff/superuser): {total_usuarios}")
        print()

        # Resumen por país
        cursor.execute(
            """
            SELECT 
                pais,
                COUNT(*) as total,
                SUM(CASE WHEN plan = 'trial' THEN 1 ELSE 0 END) as trials,
                SUM(CASE WHEN plan != 'trial' THEN 1 ELSE 0 END) as pagadas
            FROM taller_empresa
            WHERE suscripcion_activa = 1
            GROUP BY pais
            ORDER BY pais
        """
        )
        paises_stats = cursor.fetchall()

        print("=" * 80)
        print("🌍 RESUMEN POR PAÍS")
        print("=" * 80)
        for row in paises_stats:
            pais_codigo = row["pais"]
            total = row["total"]
            trials = row["trials"]
            pagadas = row["pagadas"]
            pais_nombre = obtener_nombre_pais(pais_codigo)
            print(f"\n{pais_nombre} ({pais_codigo}):")
            print(f"  Total Empresas Activas: {total}")
            print(f"  - Trials: {trials}")
            print(f"  - Pagadas: {pagadas}")
        print()

        # Detalle por país
        cursor.execute(
            "SELECT DISTINCT pais FROM taller_empresa WHERE suscripcion_activa = 1 ORDER BY pais"
        )
        paises = [row["pais"] for row in cursor.fetchall()]

        for pais_codigo in paises:
            pais_nombre = obtener_nombre_pais(pais_codigo)
            print("=" * 80)
            print(f"🌍 PAÍS: {pais_nombre} ({pais_codigo})")
            print("=" * 80)

            # Empresas activas
            cursor.execute(
                """
                SELECT 
                    e.id,
                    e.nombre_taller,
                    e.plan,
                    e.fecha_inicio,
                    e.fecha_fin,
                    e.direccion,
                    e.telefono,
                    u.username,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.date_joined
                FROM taller_empresa e
                LEFT JOIN auth_user u ON e.user_id = u.id
                WHERE e.pais = %s AND e.suscripcion_activa = 1
                ORDER BY e.nombre_taller
            """,
                (pais_codigo,),
            )

            empresas = cursor.fetchall()

            print(f"\n🏢 EMPRESAS CON SUSCRIPCIÓN ACTIVA: {len(empresas)}")
            print("-" * 80)

            if empresas:
                for idx, emp in enumerate(empresas, 1):
                    es_trial = "TRIAL" if emp["plan"] == "trial" else (emp["plan"] or "N/A").upper()
                    print(f"\n  {idx}. ✅ ACTIVA - {emp['nombre_taller'] or 'N/A'}")
                    print(f"     Usuario: {emp['username'] or 'N/A'}")
                    print(f"     Email: {emp['email'] or 'N/A'}")
                    nombre_completo = f"{emp['first_name'] or ''} {emp['last_name'] or ''}".strip()
                    if nombre_completo:
                        print(f"     Nombre: {nombre_completo}")
                    print(f"     Plan: {es_trial}")
                    print(f"     Fecha Inicio: {formatear_fecha(emp['fecha_inicio'])}")
                    print(f"     Fecha Fin: {formatear_fecha(emp['fecha_fin'])}")
                    print(f"     Dirección: {emp['direccion'] or 'N/A'}")
                    print(f"     Teléfono: {emp['telefono'] or 'N/A'}")
                    print(f"     Fecha Registro: {formatear_fecha(emp['date_joined'])}")
            else:
                print("  ⚠️  No hay empresas activas en este país")

            # Suscripciones
            cursor.execute(
                """
                SELECT 
                    s.id,
                    s.tipo,
                    s.activa,
                    s.fecha_inicio,
                    s.fecha_fin,
                    u.username,
                    u.email,
                    e.nombre_taller
                FROM taller_suscripcion s
                LEFT JOIN auth_user u ON s.user_id = u.id
                LEFT JOIN taller_empresa e ON u.id = e.user_id
                WHERE e.pais = %s AND s.activa = 1
                ORDER BY u.username
            """,
                (pais_codigo,),
            )

            suscripciones = cursor.fetchall()

            print(f"\n📋 SUSCRIPCIONES (Modelo Suscripcion): {len(suscripciones)}")
            print("-" * 80)

            if suscripciones:
                for idx, susc in enumerate(suscripciones, 1):
                    es_trial = (
                        "TRIAL" if susc["tipo"] == "trial" else (susc["tipo"] or "N/A").upper()
                    )
                    print(f"\n  {idx}. ✅ ACTIVA - {susc['username'] or 'N/A'}")
                    print(f"     Email: {susc['email'] or 'N/A'}")
                    print(f"     Tipo: {es_trial}")
                    print(f"     Fecha Inicio: {formatear_fecha(susc['fecha_inicio'])}")
                    print(f"     Fecha Fin: {formatear_fecha(susc['fecha_fin'])}")
                    print(f"     Empresa: {susc['nombre_taller'] or 'N/A'}")
            else:
                print("  ⚠️  No hay suscripciones activas en este país")

            # Trials
            cursor.execute(
                """
                SELECT 
                    t.nombre,
                    t.email,
                    t.telefono,
                    t.fecha_registro,
                    t.fecha_activacion,
                    e.nombre_taller
                FROM taller_trialregistro t
                LEFT JOIN taller_empresa e ON t.email = e.email AND e.pais = %s
                WHERE t.prueba_activa = 1
                ORDER BY t.fecha_registro
            """,
                (pais_codigo,),
            )

            trials = cursor.fetchall()

            print(f"\n🧪 CUENTAS DE PRUEBA (TRIALS) ACTIVAS: {len(trials)}")
            print("-" * 80)

            if trials:
                for idx, trial in enumerate(trials, 1):
                    print(f"\n  {idx}. ✅ ACTIVA - {trial['nombre'] or 'N/A'}")
                    print(f"     Email: {trial['email'] or 'N/A'}")
                    print(f"     Teléfono: {trial['telefono'] or 'N/A'}")
                    print(f"     Fecha Registro: {formatear_fecha(trial['fecha_registro'])}")
                    print(f"     Fecha Activación: {formatear_fecha(trial['fecha_activacion'])}")
                    print(f"     Empresa: {trial['nombre_taller'] or 'N/A'}")
            else:
                print("  ⚠️  No hay trials activos en este país")

            print()

        # Todos los trials
        cursor.execute(
            """
            SELECT 
                t.nombre,
                t.email,
                t.fecha_registro,
                t.fecha_activacion,
                e.pais
            FROM taller_trialregistro t
            LEFT JOIN taller_empresa e ON t.email = e.email
            WHERE t.prueba_activa = 1
            ORDER BY t.fecha_registro
        """
        )

        todos_trials = cursor.fetchall()

        print("=" * 80)
        print("🧪 TODAS LAS CUENTAS DE PRUEBA ACTIVAS (TRIALS)")
        print("=" * 80)
        if todos_trials:
            for idx, trial in enumerate(todos_trials, 1):
                pais_nombre = obtener_nombre_pais(trial["pais"]) if trial["pais"] else "N/A"
                print(f"\n  {idx}. {trial['nombre'] or 'N/A'} ({pais_nombre})")
                print(f"     Email: {trial['email'] or 'N/A'}")
                print(f"     Fecha Registro: {formatear_fecha(trial['fecha_registro'])}")
                print(f"     Fecha Activación: {formatear_fecha(trial['fecha_activacion'])}")
        else:
            print("  ⚠️  No hay trials activos en el sistema")

        print()
        print("=" * 80)
        print("✅ Reporte completado")
        print("=" * 80)

    connection.close()

except ImportError:
    print("❌ pymysql no está instalado.")
    print("Instálalo con: pip install pymysql")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
