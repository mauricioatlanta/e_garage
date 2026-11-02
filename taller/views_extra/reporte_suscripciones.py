"""
Vista para mostrar reporte completo de suscripciones activas.
Accesible desde: /admin/reporte-suscripciones/
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.models.trial import TrialRegistro


@staff_member_required
def reporte_suscripciones_completo(request):
    """
    Reporte completo de todas las suscripciones activas por país.
    Muestra: empresas, suscripciones, trials y usuarios registrados.
    """

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

    output = []
    output.append("=" * 80)
    output.append("📊 REPORTE DE SUSCRIPCIONES ACTIVAS")
    output.append("=" * 80)
    output.append(f"Fecha de consulta: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")

    # Estadísticas generales
    total_suscripciones = Suscripcion.objects.filter(activa=True).count()
    total_empresas_activas = Empresa.objects.filter(suscripcion_activa=True).count()
    total_trials_activos = TrialRegistro.objects.filter(prueba_activa=True).count()
    from django.contrib.auth.models import User

    total_usuarios = User.objects.filter(is_active=True, is_staff=False, is_superuser=False).count()

    output.append("📈 ESTADÍSTICAS GENERALES")
    output.append("-" * 80)
    output.append(f"Total Suscripciones Activas (modelo Suscripcion): {total_suscripciones}")
    output.append(f"Total Empresas con Suscripción Activa: {total_empresas_activas}")
    output.append(f"Total Trials Activos: {total_trials_activos}")
    output.append(f"Total Usuarios Registrados (no staff/superuser): {total_usuarios}")
    output.append("")

    # Obtener todos los países únicos
    paises_empresas = set(Empresa.objects.values_list("pais", flat=True).distinct())
    paises_todos = sorted(paises_empresas) if paises_empresas else ["CL", "US", "MX"]

    # Por cada país
    for pais_codigo in paises_todos:
        pais_nombre = obtener_nombre_pais(pais_codigo)
        output.append("=" * 80)
        output.append(f"🌍 PAÍS: {pais_nombre} ({pais_codigo})")
        output.append("=" * 80)

        # 1. Suscripciones del modelo Suscripcion
        output.append("\n📋 SUSCRIPCIONES (Modelo Suscripcion)")
        output.append("-" * 80)
        suscripciones = Suscripcion.objects.filter(
            activa=True, user__empresa__pais=pais_codigo
        ).select_related("user", "user__empresa")

        if suscripciones.exists():
            for idx, susc in enumerate(suscripciones, 1):
                vencida = susc.esta_vencida() if hasattr(susc, "esta_vencida") else False
                estado = "❌ VENCIDA" if vencida else "✅ ACTIVA"
                es_trial = susc.es_prueba() if hasattr(susc, "es_prueba") else susc.tipo == "trial"
                output.append(f"\n  {idx}. {estado} - {susc.user.username}")
                output.append(f"     Email: {susc.user.email}")
                output.append(f"     Tipo: {susc.tipo} {'(TRIAL)' if es_trial else ''}")
                output.append(f"     Fecha Inicio: {formatear_fecha(susc.fecha_inicio)}")
                output.append(f"     Fecha Fin: {formatear_fecha(susc.fecha_fin)}")
                if hasattr(susc.user, "empresa"):
                    empresa = susc.user.empresa
                    output.append(f"     Empresa: {empresa.nombre_taller}")
                    output.append(f"     Dirección: {empresa.direccion or 'N/A'}")
        else:
            output.append("  ⚠️  No hay suscripciones activas en este país")

        # 2. Empresas con suscripción activa
        output.append("\n🏢 EMPRESAS CON SUSCRIPCIÓN ACTIVA")
        output.append("-" * 80)
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
                output.append(f"\n  {idx}. {estado} - {emp.nombre_taller}")
                output.append(f"     Usuario: {emp.user.username}")
                output.append(f"     Email: {emp.user.email}")
                output.append(f"     Plan: {emp.plan} {'(TRIAL)' if es_trial else ''}")
                output.append(f"     Fecha Inicio: {formatear_fecha(emp.fecha_inicio)}")
                output.append(f"     Fecha Fin: {formatear_fecha(emp.fecha_fin)}")
                output.append(
                    f"     Días Restantes: {emp.dias_restantes if hasattr(emp, 'dias_restantes') else 'N/A'}"
                )
                output.append(f"     Dirección: {emp.direccion or 'N/A'}")
                output.append(f"     Teléfono: {emp.telefono or 'N/A'}")
        else:
            output.append("  ⚠️  No hay empresas con suscripción activa en este país")

        # 3. Trials activos
        output.append("\n🧪 CUENTAS DE PRUEBA (TRIALS) ACTIVAS")
        output.append("-" * 80)
        trials = TrialRegistro.objects.filter(prueba_activa=True)
        trials_pais = []
        for trial in trials:
            empresa_trial = Empresa.objects.filter(email=trial.email, pais=pais_codigo).first()
            if empresa_trial:
                trials_pais.append((trial, empresa_trial))

        if trials_pais:
            for idx, (trial, empresa) in enumerate(trials_pais, 1):
                dias_rest = trial.dias_restantes() if hasattr(trial, "dias_restantes") else "N/A"
                output.append(f"\n  {idx}. ✅ ACTIVA - {trial.nombre}")
                output.append(f"     Email: {trial.email}")
                output.append(f"     Teléfono: {trial.telefono}")
                output.append(f"     Fecha Registro: {formatear_fecha(trial.fecha_registro)}")
                output.append(f"     Fecha Activación: {formatear_fecha(trial.fecha_activacion)}")
                output.append(f"     Días Restantes: {dias_rest}")
                output.append(f"     Empresa: {empresa.nombre_taller if empresa else 'N/A'}")
        else:
            output.append("  ⚠️  No hay trials activos registrados en este país")

        # 4. Usuarios registrados
        output.append("\n👥 USUARIOS REGISTRADOS")
        output.append("-" * 80)
        usuarios = User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False, empresa__pais=pais_codigo
        ).select_related("empresa")

        if usuarios.exists():
            for idx, user in enumerate(usuarios, 1):
                tiene_suscripcion = hasattr(user, "suscripcion") and user.suscripcion.activa
                estado_susc = "✅ Con Suscripción" if tiene_suscripcion else "⚠️  Sin Suscripción"
                output.append(f"\n  {idx}. {estado_susc} - {user.username}")
                output.append(f"     Email: {user.email}")
                output.append(f"     Nombre: {user.first_name} {user.last_name}")
                output.append(f"     Fecha Registro: {formatear_fecha(user.date_joined)}")
                if hasattr(user, "empresa"):
                    output.append(f"     Empresa: {user.empresa.nombre_taller}")
                    output.append(f"     Plan Empresa: {user.empresa.plan}")
        else:
            output.append("  ⚠️  No hay usuarios registrados en este país")

        output.append("")

    # Resumen final
    output.append("=" * 80)
    output.append("📊 RESUMEN FINAL")
    output.append("=" * 80)
    output.append(f"Total de países con actividad: {len(paises_todos)}")
    output.append(f"Países: {', '.join([obtener_nombre_pais(p) for p in paises_todos])}")
    output.append("")

    # Todos los trials activos
    output.append("=" * 80)
    output.append("🧪 TODAS LAS CUENTAS DE PRUEBA ACTIVAS (TRIALS)")
    output.append("=" * 80)
    todos_trials = TrialRegistro.objects.filter(prueba_activa=True).order_by("fecha_registro")
    if todos_trials.exists():
        for idx, trial in enumerate(todos_trials, 1):
            empresa_trial = Empresa.objects.filter(email=trial.email).first()
            pais_trial = empresa_trial.pais if empresa_trial else "N/A"
            output.append(f"\n  {idx}. {trial.nombre} ({obtener_nombre_pais(pais_trial)})")
            output.append(f"     Email: {trial.email}")
            output.append(f"     Fecha Registro: {formatear_fecha(trial.fecha_registro)}")
            output.append(f"     Fecha Activación: {formatear_fecha(trial.fecha_activacion)}")
    else:
        output.append("  ⚠️  No hay trials activos en el sistema")

    output.append("")
    output.append("=" * 80)
    output.append("✅ Reporte completado")
    output.append("=" * 80)

    # Retornar como respuesta HTTP con formato de texto plano
    response = HttpResponse("\n".join(output), content_type="text/plain; charset=utf-8")
    return response
