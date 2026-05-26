#!/usr/bin/env python
"""
Script para consultar suscripciones en DigitalOcean.
Usa la conexión de Django directamente sin cargar toda la configuración.
Ejecutar: python tools/consultar_suscripciones_pa.py
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

# Configurar Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Importar solo la conexión de base de datos sin cargar toda la app
import django
from django.conf import settings

# Configurar Django de forma mínima
try:
    django.setup()
except Exception as e:
    print(f"⚠️  Advertencia: {e}")
    pass

# Usar la conexión de Django directamente
from django.db import connection


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

# Consulta 1: Estadísticas generales
with connection.cursor() as cursor:
    # Total empresas activas
    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM taller_empresa
        WHERE suscripcion_activa = 1
    """
    )
    total_empresas = cursor.fetchone()[0]

    # Total suscripciones activas
    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM taller_suscripcion
        WHERE activa = 1
    """
    )
    total_suscripciones = cursor.fetchone()[0]

    # Total trials activos
    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM taller_trialregistro
        WHERE prueba_activa = 1
    """
    )
    total_trials = cursor.fetchone()[0]

    # Total usuarios (no staff/superuser)
    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM auth_user
        WHERE is_active = 1 AND is_staff = 0 AND is_superuser = 0
    """
    )
    total_usuarios = cursor.fetchone()[0]

print("📈 ESTADÍSTICAS GENERALES")
print("-" * 80)
print(f"Total Empresas con Suscripción Activa: {total_empresas}")
print(f"Total Suscripciones Activas (modelo Suscripcion): {total_suscripciones}")
print(f"Total Trials Activos: {total_trials}")
print(f"Total Usuarios Registrados (no staff/superuser): {total_usuarios}")
print()

# Consulta 2: Empresas por país
with connection.cursor() as cursor:
    cursor.execute(
        """
        SELECT 
            e.pais,
            COUNT(*) as total,
            SUM(CASE WHEN e.plan = 'trial' THEN 1 ELSE 0 END) as trials,
            SUM(CASE WHEN e.plan != 'trial' THEN 1 ELSE 0 END) as pagadas
        FROM taller_empresa e
        WHERE e.suscripcion_activa = 1
        GROUP BY e.pais
        ORDER BY e.pais
    """
    )
    paises_stats = cursor.fetchall()

print("=" * 80)
print("🌍 RESUMEN POR PAÍS")
print("=" * 80)
for pais_codigo, total, trials, pagadas in paises_stats:
    pais_nombre = obtener_nombre_pais(pais_codigo)
    print(f"\n{pais_nombre} ({pais_codigo}):")
    print(f"  Total Empresas Activas: {total}")
    print(f"  - Trials: {trials}")
    print(f"  - Pagadas: {pagadas}")
print()

# Consulta 3: Detalle de empresas activas por país
with connection.cursor() as cursor:
    cursor.execute(
        """
        SELECT DISTINCT pais
        FROM taller_empresa
        WHERE suscripcion_activa = 1
        ORDER BY pais
    """
    )
    paises = [row[0] for row in cursor.fetchall()]

for pais_codigo in paises:
    pais_nombre = obtener_nombre_pais(pais_codigo)
    print("=" * 80)
    print(f"🌍 PAÍS: {pais_nombre} ({pais_codigo})")
    print("=" * 80)

    # Empresas activas
    with connection.cursor() as cursor:
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
            [pais_codigo],
        )

        empresas = cursor.fetchall()

    print(f"\n🏢 EMPRESAS CON SUSCRIPCIÓN ACTIVA: {len(empresas)}")
    print("-" * 80)

    if empresas:
        for idx, emp in enumerate(empresas, 1):
            (
                emp_id,
                nombre,
                plan,
                fecha_inicio,
                fecha_fin,
                direccion,
                telefono,
                username,
                email,
                first_name,
                last_name,
                date_joined,
            ) = emp
            es_trial = "TRIAL" if plan == "trial" else plan.upper() if plan else "N/A"

            print(f"\n  {idx}. ✅ ACTIVA - {nombre}")
            print(f"     Usuario: {username or 'N/A'}")
            print(f"     Email: {email or 'N/A'}")
            print(f"     Nombre: {first_name or ''} {last_name or ''}".strip())
            print(f"     Plan: {es_trial}")
            print(f"     Fecha Inicio: {formatear_fecha(fecha_inicio)}")
            print(f"     Fecha Fin: {formatear_fecha(fecha_fin)}")
            print(f"     Dirección: {direccion or 'N/A'}")
            print(f"     Teléfono: {telefono or 'N/A'}")
            print(f"     Fecha Registro: {formatear_fecha(date_joined)}")
    else:
        print("  ⚠️  No hay empresas activas en este país")

    # Suscripciones del modelo Suscripcion
    with connection.cursor() as cursor:
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
            [pais_codigo],
        )

        suscripciones = cursor.fetchall()

    print(f"\n📋 SUSCRIPCIONES (Modelo Suscripcion): {len(suscripciones)}")
    print("-" * 80)

    if suscripciones:
        for idx, susc in enumerate(suscripciones, 1):
            susc_id, tipo, activa, fecha_inicio, fecha_fin, username, email, nombre_taller = susc
            es_trial = "TRIAL" if tipo == "trial" else tipo.upper() if tipo else "N/A"

            print(f"\n  {idx}. ✅ ACTIVA - {username or 'N/A'}")
            print(f"     Email: {email or 'N/A'}")
            print(f"     Tipo: {es_trial}")
            print(f"     Fecha Inicio: {formatear_fecha(fecha_inicio)}")
            print(f"     Fecha Fin: {formatear_fecha(fecha_fin)}")
            print(f"     Empresa: {nombre_taller or 'N/A'}")
    else:
        print("  ⚠️  No hay suscripciones activas en este país")

    # Trials activos
    with connection.cursor() as cursor:
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
            [pais_codigo],
        )

        trials = cursor.fetchall()

    print(f"\n🧪 CUENTAS DE PRUEBA (TRIALS) ACTIVAS: {len(trials)}")
    print("-" * 80)

    if trials:
        for idx, trial in enumerate(trials, 1):
            nombre, email, telefono, fecha_registro, fecha_activacion, nombre_taller = trial
            print(f"\n  {idx}. ✅ ACTIVA - {nombre or 'N/A'}")
            print(f"     Email: {email or 'N/A'}")
            print(f"     Teléfono: {telefono or 'N/A'}")
            print(f"     Fecha Registro: {formatear_fecha(fecha_registro)}")
            print(f"     Fecha Activación: {formatear_fecha(fecha_activacion)}")
            print(f"     Empresa: {nombre_taller or 'N/A'}")
    else:
        print("  ⚠️  No hay trials activos en este país")

    print()

# Resumen final
print("=" * 80)
print("📊 RESUMEN FINAL")
print("=" * 80)
print(f"Total de países con actividad: {len(paises)}")
print(f"Países: {', '.join([obtener_nombre_pais(p) for p in paises])}")
print()

# Todos los trials activos
with connection.cursor() as cursor:
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
        nombre, email, fecha_registro, fecha_activacion, pais = trial
        pais_nombre = obtener_nombre_pais(pais) if pais else "N/A"
        print(f"\n  {idx}. {nombre or 'N/A'} ({pais_nombre})")
        print(f"     Email: {email or 'N/A'}")
        print(f"     Fecha Registro: {formatear_fecha(fecha_registro)}")
        print(f"     Fecha Activación: {formatear_fecha(fecha_activacion)}")
else:
    print("  ⚠️  No hay trials activos en el sistema")

print()
print("=" * 80)
print("✅ Reporte completado")
print("=" * 80)
