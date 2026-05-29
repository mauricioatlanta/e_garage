"""
Vista de reporte del embudo de registro
"""

from datetime import datetime, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone

from taller.models.registro_embudo import RegistroEmbudoSuscriptor


@staff_member_required
def reporte_embudo_registro(request):
    """
    Reporte del embudo de registro por país y fechas.

    Parámetros GET:
    - from: fecha inicio (YYYY-MM-DD)
    - to: fecha fin (YYYY-MM-DD)
    """
    # Obtener parámetros de fecha
    from_date = request.GET.get("from")
    to_date = request.GET.get("to")

    # Parsear fechas o usar defaults
    if from_date:
        try:
            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        except ValueError:
            from_date = None
    if not from_date:
        from_date = timezone.now().date() - timedelta(days=30)  # Últimos 30 días

    if to_date:
        try:
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            to_date = None
    if not to_date:
        to_date = timezone.now().date()

    # Filtrar por fechas
    queryset = RegistroEmbudoSuscriptor.objects.filter(
        fecha_registro__date__gte=from_date, fecha_registro__date__lte=to_date
    )

    # Obtener países únicos
    paises = queryset.values_list("pais", flat=True).distinct()

    # Calcular métricas por país
    datos_por_pais = []
    for pais in sorted(paises):
        registros_pais = queryset.filter(pais=pais)

        total_registros = registros_pais.count()
        total_email_confirmado = registros_pais.filter(email_confirmado_at__isnull=False).count()
        total_primer_login = registros_pais.filter(primer_login_at__isnull=False).count()
        total_empresa_creada = registros_pais.filter(empresa_creada_at__isnull=False).count()
        total_obtuvo_trial = registros_pais.filter(obtuvo_trial=True).count()

        # Calcular tasas de conversión
        tasa_email_confirmado = (
            (total_email_confirmado / total_registros * 100) if total_registros > 0 else 0
        )
        tasa_primer_login = (
            (total_primer_login / total_email_confirmado * 100) if total_email_confirmado > 0 else 0
        )
        tasa_empresa_creada = (
            (total_empresa_creada / total_primer_login * 100) if total_primer_login > 0 else 0
        )

        datos_por_pais.append(
            {
                "pais": pais,
                "total_registros": total_registros,
                "total_email_confirmado": total_email_confirmado,
                "total_primer_login": total_primer_login,
                "total_empresa_creada": total_empresa_creada,
                "total_obtuvo_trial": total_obtuvo_trial,
                "tasa_email_confirmado": round(tasa_email_confirmado, 2),
                "tasa_primer_login": round(tasa_primer_login, 2),
                "tasa_empresa_creada": round(tasa_empresa_creada, 2),
            }
        )

    # Totales generales
    totales = {
        "total_registros": queryset.count(),
        "total_email_confirmado": queryset.filter(email_confirmado_at__isnull=False).count(),
        "total_primer_login": queryset.filter(primer_login_at__isnull=False).count(),
        "total_empresa_creada": queryset.filter(empresa_creada_at__isnull=False).count(),
        "total_obtuvo_trial": queryset.filter(obtuvo_trial=True).count(),
    }

    context = {
        "datos_por_pais": datos_por_pais,
        "totales": totales,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "taller/reportes/embudo_registro.html", context)
