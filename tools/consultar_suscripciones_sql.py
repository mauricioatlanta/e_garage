#!/usr/bin/env python
"""
Script alternativo para consultar suscripciones usando SQL directo.
Este script evita el problema de configuración de Django con allauth.
Ejecutar: python tools/consultar_suscripciones_sql.py
"""

import os
import sys
from pathlib import Path

# Configurar el path base
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Cargar variables de entorno
from dotenv import load_dotenv

load_dotenv()

# Configurar Django con settings mínimos
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Importar solo lo necesario para la conexión a la BD
import django
from django.conf import settings

# Configurar Django sin cargar todas las apps
try:
    # Intentar configurar Django
    django.setup()
except Exception as e:
    print(f"⚠️  Advertencia al configurar Django: {e}")
    print("Intentando continuar con configuración mínima...")

# Ahora importar modelos (después de setup)
try:
    from django.db import connection
    from django.contrib.auth.models import User
    from taller.models.suscripcion import Suscripcion
    from taller.models.empresa import Empresa
    from taller.models.trial import TrialRegistro
    from django.utils import timezone
except Exception as e:
    print(f"❌ Error importando modelos: {e}")
    print("\nIntentando consulta SQL directa...")

    # Consulta SQL directa como alternativa
    import mysql.connector
    from mysql.connector import Error

    try:
        # Obtener credenciales de .env
        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "database": os.getenv("DB_NAME", "egarage"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
        }

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        print("=" * 80)
        print("📊 REPORTE DE SUSCRIPCIONES ACTIVAS (SQL Directo)")
        print("=" * 80)

        # Consultar empresas activas
        query = """
        SELECT e.id, e.nombre_taller, e.pais, e.plan, e.suscripcion_activa,
               e.fecha_inicio, e.fecha_fin, u.username, u.email, u.first_name, u.last_name
        FROM taller_empresa e
        LEFT JOIN auth_user u ON e.user_id = u.id
        WHERE e.suscripcion_activa = 1
        ORDER BY e.pais, e.nombre_taller
        """

        cursor.execute(query)
        empresas = cursor.fetchall()

        print(f"\n📈 Total Empresas Activas: {len(empresas)}")
        print("\n" + "=" * 80)

        # Agrupar por país
        paises = {}
        for emp in empresas:
            pais = emp.get("pais", "N/A")
            if pais not in paises:
                paises[pais] = []
            paises[pais].append(emp)

        for pais_codigo in sorted(paises.keys()):
            pais_nombre = {
                "CL": "Chile",
                "US": "Estados Unidos",
                "MX": "México",
            }.get(pais_codigo, pais_codigo)

            print(f"\n🌍 PAÍS: {pais_nombre} ({pais_codigo})")
            print("-" * 80)

            for idx, emp in enumerate(paises[pais_codigo], 1):
                es_trial = "TRIAL" if emp.get("plan") == "trial" else emp.get("plan", "N/A").upper()
                print(f"\n  {idx}. ✅ ACTIVA - {emp.get('nombre_taller', 'N/A')}")
                print(f"     Usuario: {emp.get('username', 'N/A')}")
                print(f"     Email: {emp.get('email', 'N/A')}")
                print(f"     Plan: {es_trial}")
                print(f"     Fecha Inicio: {emp.get('fecha_inicio', 'N/A')}")
                print(f"     Fecha Fin: {emp.get('fecha_fin', 'N/A')}")

        # Consultar suscripciones
        query_susc = """
        SELECT s.id, s.tipo, s.activa, s.fecha_inicio, s.fecha_fin,
               u.username, u.email, e.pais, e.nombre_taller
        FROM taller_suscripcion s
        LEFT JOIN auth_user u ON s.user_id = u.id
        LEFT JOIN taller_empresa e ON u.id = e.user_id
        WHERE s.activa = 1
        ORDER BY e.pais, u.username
        """

        cursor.execute(query_susc)
        suscripciones = cursor.fetchall()

        print("\n" + "=" * 80)
        print(f"📋 SUSCRIPCIONES ACTIVAS: {len(suscripciones)}")
        print("=" * 80)

        for idx, susc in enumerate(suscripciones, 1):
            es_trial = "TRIAL" if susc.get("tipo") == "trial" else susc.get("tipo", "N/A").upper()
            print(f"\n  {idx}. ✅ ACTIVA - {susc.get('username', 'N/A')}")
            print(f"     Email: {susc.get('email', 'N/A')}")
            print(f"     Tipo: {es_trial}")
            print(f"     País: {susc.get('pais', 'N/A')}")
            print(f"     Empresa: {susc.get('nombre_taller', 'N/A')}")

        # Consultar trials
        query_trials = """
        SELECT nombre, email, telefono, fecha_registro, fecha_activacion, prueba_activa
        FROM taller_trialregistro
        WHERE prueba_activa = 1
        ORDER BY fecha_registro
        """

        cursor.execute(query_trials)
        trials = cursor.fetchall()

        print("\n" + "=" * 80)
        print(f"🧪 TRIALS ACTIVOS: {len(trials)}")
        print("=" * 80)

        for idx, trial in enumerate(trials, 1):
            print(f"\n  {idx}. ✅ ACTIVA - {trial.get('nombre', 'N/A')}")
            print(f"     Email: {trial.get('email', 'N/A')}")
            print(f"     Teléfono: {trial.get('telefono', 'N/A')}")
            print(f"     Fecha Registro: {trial.get('fecha_registro', 'N/A')}")

        cursor.close()
        connection.close()

        print("\n" + "=" * 80)
        print("✅ Reporte completado")
        print("=" * 80)

        sys.exit(0)

    except Error as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        sys.exit(1)


# Si llegamos aquí, Django funcionó correctamente
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
    if hasattr(fecha, "strftime"):
        return fecha.strftime("%Y-%m-%d %H:%M:%S")
    return str(fecha)


print("=" * 80)
print("📊 REPORTE DE SUSCRIPCIONES ACTIVAS")
print("=" * 80)
print(f"Fecha de consulta: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

try:
    # Estadísticas generales
    total_suscripciones = Suscripcion.objects.filter(activa=True).count()
    total_empresas_activas = Empresa.objects.filter(suscripcion_activa=True).count()
    total_trials_activos = TrialRegistro.objects.filter(prueba_activa=True).count()
    total_usuarios = User.objects.filter(is_active=True, is_staff=False, is_superuser=False).count()

    print("📈 ESTADÍSTICAS GENERALES")
    print("-" * 80)
    print(f"Total Suscripciones Activas (modelo Suscripcion): {total_suscripciones}")
    print(f"Total Empresas con Suscripción Activa: {total_empresas_activas}")
    print(f"Total Trials Activos: {total_trials_activos}")
    print(f"Total Usuarios Registrados (no staff/superuser): {total_usuarios}")
    print()

    # Obtener todos los países únicos
    paises_empresas = set(Empresa.objects.values_list("pais", flat=True).distinct())
    paises_todos = sorted(paises_empresas) if paises_empresas else ["CL", "US", "MX"]

    # Por cada país
    for pais_codigo in paises_todos:
        pais_nombre = obtener_nombre_pais(pais_codigo)
        print("=" * 80)
        print(f"🌍 PAÍS: {pais_nombre} ({pais_codigo})")
        print("=" * 80)

        # 1. Suscripciones del modelo Suscripcion
        print("\n📋 SUSCRIPCIONES (Modelo Suscripcion)")
        print("-" * 80)
        suscripciones = Suscripcion.objects.filter(
            activa=True, user__empresa__pais=pais_codigo
        ).select_related("user", "user__empresa")

        if suscripciones.exists():
            for idx, susc in enumerate(suscripciones, 1):
                vencida = susc.esta_vencida() if hasattr(susc, "esta_vencida") else False
                estado = "❌ VENCIDA" if vencida else "✅ ACTIVA"
                es_trial = susc.es_prueba() if hasattr(susc, "es_prueba") else susc.tipo == "trial"
                print(f"\n  {idx}. {estado} - {susc.user.username}")
                print(f"     Email: {susc.user.email}")
                print(f"     Tipo: {susc.tipo} {'(TRIAL)' if es_trial else ''}")
                print(f"     Fecha Inicio: {formatear_fecha(susc.fecha_inicio)}")
                print(f"     Fecha Fin: {formatear_fecha(susc.fecha_fin)}")
                if hasattr(susc.user, "empresa"):
                    empresa = susc.user.empresa
                    print(f"     Empresa: {empresa.nombre_taller}")
                    print(f"     Dirección: {empresa.direccion or 'N/A'}")
        else:
            print("  ⚠️  No hay suscripciones activas en este país")

        # 2. Empresas con suscripción activa
        print("\n🏢 EMPRESAS CON SUSCRIPCIÓN ACTIVA")
        print("-" * 80)
        empresas = Empresa.objects.filter(pais=pais_codigo, suscripcion_activa=True).select_related(
            "user"
        )

        if empresas.exists():
            for idx, emp in enumerate(empresas, 1):
                vencida = (
                    timezone.now() > emp.fecha_expiracion
                    if hasattr(emp, "fecha_expiracion")
                    else False
                )
                estado = "❌ VENCIDA" if vencida else "✅ ACTIVA"
                es_trial = emp.plan == "trial"
                print(f"\n  {idx}. {estado} - {emp.nombre_taller}")
                print(f"     Usuario: {emp.user.username}")
                print(f"     Email: {emp.user.email}")
                print(f"     Plan: {emp.plan} {'(TRIAL)' if es_trial else ''}")
                print(f"     Fecha Inicio: {formatear_fecha(emp.fecha_inicio)}")
                print(f"     Fecha Fin: {formatear_fecha(emp.fecha_fin)}")
                print(
                    f"     Días Restantes: {emp.dias_restantes if hasattr(emp, 'dias_restantes') else 'N/A'}"
                )
                print(f"     Dirección: {emp.direccion or 'N/A'}")
                print(f"     Teléfono: {emp.telefono or 'N/A'}")
        else:
            print("  ⚠️  No hay empresas con suscripción activa en este país")

        # 3. Trials activos
        print("\n🧪 CUENTAS DE PRUEBA (TRIALS) ACTIVAS")
        print("-" * 80)
        trials = TrialRegistro.objects.filter(prueba_activa=True)
        trials_pais = []
        for trial in trials:
            empresa_trial = Empresa.objects.filter(email=trial.email, pais=pais_codigo).first()
            if empresa_trial:
                trials_pais.append((trial, empresa_trial))

        if trials_pais:
            for idx, (trial, empresa) in enumerate(trials_pais, 1):
                dias_rest = trial.dias_restantes() if hasattr(trial, "dias_restantes") else "N/A"
                print(f"\n  {idx}. ✅ ACTIVA - {trial.nombre}")
                print(f"     Email: {trial.email}")
                print(f"     Teléfono: {trial.telefono}")
                print(f"     Fecha Registro: {formatear_fecha(trial.fecha_registro)}")
                print(f"     Fecha Activación: {formatear_fecha(trial.fecha_activacion)}")
                print(f"     Días Restantes: {dias_rest}")
                print(f"     Empresa: {empresa.nombre_taller if empresa else 'N/A'}")
        else:
            print("  ⚠️  No hay trials activos registrados en este país")

        # 4. Usuarios registrados
        print("\n👥 USUARIOS REGISTRADOS")
        print("-" * 80)
        usuarios = User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False, empresa__pais=pais_codigo
        ).select_related("empresa")

        if usuarios.exists():
            for idx, user in enumerate(usuarios, 1):
                tiene_suscripcion = hasattr(user, "suscripcion") and user.suscripcion.activa
                estado_susc = "✅ Con Suscripción" if tiene_suscripcion else "⚠️  Sin Suscripción"
                print(f"\n  {idx}. {estado_susc} - {user.username}")
                print(f"     Email: {user.email}")
                print(f"     Nombre: {user.first_name} {user.last_name}")
                print(f"     Fecha Registro: {formatear_fecha(user.date_joined)}")
                if hasattr(user, "empresa"):
                    print(f"     Empresa: {user.empresa.nombre_taller}")
                    print(f"     Plan Empresa: {user.empresa.plan}")
        else:
            print("  ⚠️  No hay usuarios registrados en este país")

        print()

    # Resumen final
    print("=" * 80)
    print("📊 RESUMEN FINAL")
    print("=" * 80)
    print(f"Total de países con actividad: {len(paises_todos)}")
    print(f"Países: {', '.join([obtener_nombre_pais(p) for p in paises_todos])}")
    print()

    # Todos los trials activos
    print("=" * 80)
    print("🧪 TODAS LAS CUENTAS DE PRUEBA ACTIVAS (TRIALS)")
    print("=" * 80)
    todos_trials = TrialRegistro.objects.filter(prueba_activa=True).order_by("fecha_registro")
    if todos_trials.exists():
        for idx, trial in enumerate(todos_trials, 1):
            empresa_trial = Empresa.objects.filter(email=trial.email).first()
            pais_trial = empresa_trial.pais if empresa_trial else "N/A"
            print(f"\n  {idx}. {trial.nombre} ({obtener_nombre_pais(pais_trial)})")
            print(f"     Email: {trial.email}")
            print(f"     Fecha Registro: {formatear_fecha(trial.fecha_registro)}")
            print(f"     Fecha Activación: {formatear_fecha(trial.fecha_activacion)}")
    else:
        print("  ⚠️  No hay trials activos en el sistema")

    print()
    print("=" * 80)
    print("✅ Reporte completado")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error al generar reporte: {str(e)}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
