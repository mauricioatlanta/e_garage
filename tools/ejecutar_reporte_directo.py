#!/usr/bin/env python
"""
Script para ejecutar el reporte de suscripciones directamente.
Ejecutar: python tools/ejecutar_reporte_directo.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar el path base
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Configurar Django antes de importar modelos
try:
    django.setup()
except Exception as e:
    print(f"Error configurando Django: {e}")
    print("Intentando continuar...")
    pass

# Ahora importar modelos
from django.contrib.auth.models import User
from taller.models.suscripcion import Suscripcion
from taller.models.empresa import Empresa
from taller.models.trial import TrialRegistro
from django.utils import timezone


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
