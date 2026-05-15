"""
Panel interno de monitoreo de suscripciones con filtros avanzados
Vista administrativa para gestiÃ³n y anÃ¡lisis de suscripciones
"""

import csv
from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from taller.models.comprobante_pago import ComprobantePago
from taller.models.empresa import Empresa
from taller.models.trial import TrialRegistro
from taller.utils.smart_logging import smart_logger


@staff_member_required
def subscription_dashboard(request):
    """Panel principal de monitoreo de suscripciones"""

    # EstadÃ­sticas generales
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    stats = {
        "total_empresas": Empresa.objects.count(),
        "activas": Empresa.objects.filter(suscripcion_activa=True).count(),
        "inactivas": Empresa.objects.filter(suscripcion_activa=False).count(),
        "trials_activos": TrialRegistro.objects.filter(prueba_activa=True).count(),
        "trials_expirados": TrialRegistro.objects.filter(prueba_expirada=True).count(),
    }

    # Empresas que vencen pronto (deshabilitado por campos legacy)
    expiring_soon = Empresa.objects.none()

    # Trials que expiran pronto (prÃ³ximos 7 dÃ­as)
    trials_expiring = TrialRegistro.objects.none()

    # Ingresos del mes
    current_month_payments = (
        ComprobantePago.objects.filter(
            fecha_subida__year=today.year,
            fecha_subida__month=today.month,
        ).aggregate(total=Sum("monto"))["total"]
        or 0
    )

    context = {
        "stats": stats,
        "expiring_soon": expiring_soon[:10],  # Mostrar solo los 10 mÃ¡s prÃ³ximos
        "trials_expiring": trials_expiring[:10],
        "current_month_revenue": current_month_payments,
        "today": today,
    }

    return render(request, "admin_panel/subscription_dashboard.html", context)


@staff_member_required
def subscription_list(request):
    """Lista detallada de suscripciones con filtros avanzados"""

    # Obtener parÃ¡metros de filtro
    status_filter = request.GET.get("status", "")
    search_query = request.GET.get("search", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    trial_filter = request.GET.get("trial", "")
    payment_status = request.GET.get("payment", "")
    sort_by = request.GET.get("sort", "-fecha_inicio")

    # Query base
    empresas = Empresa.objects.select_related("usuario").prefetch_related("comprobantes")

    # Aplicar filtros
    if status_filter == "activa":
        empresas = empresas.filter(suscripcion_activa=True)
    elif status_filter == "inactiva":
        empresas = empresas.filter(suscripcion_activa=False)

    if search_query:
        empresas = empresas.filter(
            Q(nombre_taller__icontains=search_query)
            | Q(empresa__icontains=search_query)
            | Q(usuario__username__icontains=search_query)
            | Q(usuario__email__icontains=search_query)
            | Q(usuario__first_name__icontains=search_query)
            | Q(usuario__last_name__icontains=search_query)
        )

    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d").date()
            empresas = empresas.filter(fecha_inicio__gte=date_from_parsed)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d").date()
            empresas = empresas.filter(fecha_inicio__lte=date_to_parsed)
        except ValueError:
            pass

    if trial_filter == "active":
        # Solo empresas con trial activo
        trial_ids = TrialRegistro.objects.filter(activo=True).values_list("empresa_id", flat=True)
        empresas = empresas.filter(id__in=trial_ids)
    elif trial_filter == "expired":
        # Solo empresas con trial expirado
        trial_ids = TrialRegistro.objects.filter(activo=False).values_list("empresa_id", flat=True)
        empresas = empresas.filter(id__in=trial_ids)

    if payment_status == "pending":
        # Empresas con pagos pendientes (filtro deshabilitado - campo aprobado no existe)
        pending_payment_ids = []  # disabled: legacy values_list block
        pass

    # Ordenamiento
    valid_sort_fields = [
        "fecha_inicio",
        "-fecha_inicio",
        "nombre_taller",
        "-nombre_taller",
        "suscripcion_activa",
        "-suscripcion_activa",
    ]
    if sort_by in valid_sort_fields:
        empresas = empresas.order_by(sort_by)

    # PaginaciÃ³n
    paginator = Paginator(empresas, 25)  # 25 empresas por pÃ¡gina
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Contexto para filtros
    status_choices = [
        ("activa", "Activa"),
        ("inactiva", "Inactiva"),
    ]

    trial_choices = [
        ("active", "Trial Activo"),
        ("expired", "Trial Expirado"),
    ]

    context = {
        "page_obj": page_obj,
        "status_choices": status_choices,
        "trial_choices": trial_choices,
        "current_filters": {
            "status": status_filter,
            "search": search_query,
            "date_from": date_from,
            "date_to": date_to,
            "trial": trial_filter,
            "payment": payment_status,
            "sort": sort_by,
        },
        "total_count": paginator.count,
    }

    return render(request, "admin_panel/subscription_list.html", context)


@staff_member_required
def subscription_analytics(request):
    """Analytics avanzados de suscripciones"""

    today = timezone.now().date()

    # AnÃ¡lisis temporal (Ãºltimos 12 meses)
    monthly_data = []
    for i in range(12):
        # Calcular fecha del mes de manera mÃ¡s robusta
        # Restar meses de forma segura
        target_month = today.month - i
        target_year = today.year

        # Ajustar aÃ±o si el mes es negativo
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        month_date = today.replace(year=target_year, month=target_month, day=1)
        month_start = month_date

        # Calcular fin del mes de manera segura
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(
                days=1
            )
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)

        # Nuevas suscripciones
        nuevas = Empresa.objects.filter(
            fecha_inicio__gte=month_start, fecha_inicio__lte=month_end
        ).count()

        # Cancelaciones (empresas inactivas que vencieron en este mes)
        # Nota: fecha_modificacion no existe, usamos fecha_fin como aproximaciÃ³n
        canceladas = Empresa.objects.filter(
            suscripcion_activa=False,
            fecha_fin__gte=month_start,
            fecha_fin__lte=month_end,
        ).count()

        # Ingresos
        ingresos = (
            ComprobantePago.objects.filter(
                fecha_subida__gte=month_start,
                fecha_subida__lte=month_end,
            ).aggregate(total=Sum("monto"))["total"]
            or 0
        )

        monthly_data.append(
            {
                "month": month_date.strftime("%Y-%m"),
                "month_name": month_date.strftime("%B %Y"),
                "nuevas": nuevas,
                "canceladas": canceladas,
                "ingresos": float(ingresos),
                "neto": nuevas - canceladas,
            }
        )

    monthly_data.reverse()  # Orden cronolÃ³gico

    # AnÃ¡lisis de conversiÃ³n de trials
    total_trials = TrialRegistro.objects.count()
    trials_convertidos = TrialRegistro.objects.filter(empresa__suscripcion_activa=True).count()
    conversion_rate = (trials_convertidos / total_trials * 100) if total_trials > 0 else 0

    # AnÃ¡lisis de retenciÃ³n
    empresas_activas_30_dias = Empresa.objects.filter(
        suscripcion_activa=True, fecha_inicio__lte=today - timedelta(days=30)
    ).count()

    total_empresas_30_dias = Empresa.objects.filter(
        fecha_inicio__lte=today - timedelta(days=30)
    ).count()

    retention_rate = (
        (empresas_activas_30_dias / total_empresas_30_dias * 100)
        if total_empresas_30_dias > 0
        else 0
    )

    # Top empresas por ingresos
    top_empresas = (
        Empresa.objects.annotate(total_pagos=Sum("comprobantes__monto"))
        .filter(total_pagos__isnull=False)
        .order_by("-total_pagos")[:10]
    )

    context = {
        "monthly_data": monthly_data,
        "conversion_rate": round(conversion_rate, 2),
        "retention_rate": round(retention_rate, 2),
        "total_trials": total_trials,
        "trials_convertidos": trials_convertidos,
        "top_empresas": top_empresas,
    }

    return render(request, "admin_panel/subscription_analytics.html", context)


@staff_member_required
def subscription_detail(request, empresa_id):
    """Vista detallada de una suscripciÃ³n especÃ­fica"""

    empresa = get_object_or_404(Empresa, id=empresa_id)

    # Trial asociado
    trial = TrialRegistro.objects.filter(empresa=empresa).first()

    # Historial de pagos
    pagos = ComprobantePago.objects.filter(empresa=empresa).order_by("-fecha_subida")

    # EstadÃ­sticas de uso (esto requerirÃ­a modelos adicionales de tracking)
    # Por ahora, datos bÃ¡sicos

    context = {
        "empresa": empresa,
        "trial": trial,
        "pagos": pagos,
        "total_pagos": pagos.aggregate(total=Sum("monto"))["total"] or 0,
        "pagos_pendientes": 0,  # Campo aprobado no existe
    }

    return render(request, "admin_panel/subscription_detail.html", context)


@staff_member_required
def subscription_actions(request, empresa_id):
    """Acciones administrativas sobre suscripciones"""

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    empresa = get_object_or_404(Empresa, id=empresa_id)
    action = request.POST.get("action")

    if action == "suspend":
        old_status = "activa" if empresa.suscripcion_activa else "inactiva"
        empresa.suscripcion_activa = False
        empresa.save()

        smart_logger.log_subscription_change(
            empresa_id=empresa.id,
            old_status=old_status,
            new_status="inactiva",
            reason=f"SuspensiÃ³n manual por admin: {request.user.username}",
        )

        return JsonResponse({"success": True, "message": "Empresa suspendida correctamente"})

    elif action == "activate":
        old_status = "activa" if empresa.suscripcion_activa else "inactiva"
        empresa.suscripcion_activa = True
        empresa.save()

        smart_logger.log_subscription_change(
            empresa_id=empresa.id,
            old_status=old_status,
            new_status="activa",
            reason=f"ActivaciÃ³n manual por admin: {request.user.username}",
        )

        return JsonResponse({"success": True, "message": "Empresa activada correctamente"})

    elif action == "extend":
        days = int(request.POST.get("days", 30))
        # Extender suscripciÃ³n con notificaciÃ³n automÃ¡tica
        empresa.extender_suscripcion(days, enviar_notificacion=True)

        smart_logger.log_subscription_change(
            empresa_id=empresa.id,
            old_status="activa" if empresa.suscripcion_activa else "inactiva",
            new_status="activa" if empresa.suscripcion_activa else "inactiva",
            reason=f"ExtensiÃ³n de {days} dÃ­as por admin: {request.user.username}",
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"SuscripciÃ³n extendida {days} dÃ­as. NotificaciÃ³n enviada al cliente.",
            }
        )

    else:
        return JsonResponse({"error": "AcciÃ³n no vÃ¡lida"}, status=400)


@staff_member_required
def export_subscriptions(request):
    """Exportar datos de suscripciones a CSV"""

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="suscripciones_{timezone.now().strftime("%Y%m%d")}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Empresa",
            "Usuario",
            "Email",
            "Estado",
            "Fecha Registro",
            "Fecha Vencimiento",
            "Total Pagos",
            "Trial Activo",
        ]
    )

    # Aplicar filtros si existen
    empresas = Empresa.objects.select_related("usuario").all()
    status_filter = request.GET.get("status")
    if status_filter == "activa":
        empresas = empresas.filter(suscripcion_activa=True)
    elif status_filter == "inactiva":
        empresas = empresas.filter(suscripcion_activa=False)

    for empresa in empresas:
        trial_activo = TrialRegistro.objects.filter(empresa=empresa, activo=True).exists()
        total_pagos = empresa.comprobantes.aggregate(total=Sum("monto"))["total"] or 0

        writer.writerow(
            [
                empresa.id,
                empresa.nombre_taller or empresa.empresa or "",
                empresa.usuario.username,
                empresa.usuario.email,
                "Activa" if empresa.suscripcion_activa else "Inactiva",
                empresa.fecha_inicio.strftime("%Y-%m-%d"),
                (empresa.fecha_fin.strftime("%Y-%m-%d") if empresa.fecha_fin else ""),
                total_pagos,
                "SÃ­" if trial_activo else "No",
            ]
        )

    return response


@staff_member_required
def subscription_api_stats(request):
    """API endpoint para estadÃ­sticas en tiempo real (para grÃ¡ficos AJAX)"""

    today = timezone.now().date()

    # EstadÃ­sticas por estado
    stats_by_status = [
        {
            "suscripcion_activa": True,
            "count": Empresa.objects.filter(suscripcion_activa=True).count(),
        },
        {
            "suscripcion_activa": False,
            "count": Empresa.objects.filter(suscripcion_activa=False).count(),
        },
    ]

    # Nuevas suscripciones por dÃ­a (Ãºltimos 30 dÃ­as)
    daily_new = []
    for i in range(30):
        date = today - timedelta(days=i)
        count = Empresa.objects.filter(fecha_inicio=date).count()
        daily_new.append({"date": date.strftime("%Y-%m-%d"), "count": count})

    daily_new.reverse()

    data = {
        "stats_by_status": list(stats_by_status),
        "daily_new": daily_new,
        "last_updated": timezone.now().isoformat(),
    }

    return JsonResponse(data)

