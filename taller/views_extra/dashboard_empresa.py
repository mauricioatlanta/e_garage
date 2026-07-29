from datetime import date, datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from taller.auth.decorators import country_login_required
from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo
from taller.utils.empresa import get_or_create_empresa

# --- CONSTANTS ---
SUBTOTAL_EXPR = ExpressionWrapper(
    F("precio_unitario") * F("cantidad"),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)

ZERO_DEC = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


# --- HELPER FUNCTIONS ---
def inicio_mes_datetime(hoy):
    """Devuelve inicio de mes compatible con USE_TZ=True/False."""
    inicio = datetime(hoy.year, hoy.month, 1, 0, 0, 0)
    if settings.USE_TZ:
        return timezone.make_aware(inicio, timezone.get_current_timezone())
    return inicio


def total_servicios(qs_base):
    """Calcula el total de servicios usando subtotal (precio * cantidad)"""
    return qs_base.aggregate(total=Coalesce(Sum(SUBTOTAL_EXPR), ZERO_DEC))["total"]


def total_repuestos(qs_base):
    """Calcula el total de repuestos usando subtotal (precio * cantidad)"""
    return qs_base.aggregate(total=Coalesce(Sum(SUBTOTAL_EXPR), ZERO_DEC))["total"]


@country_login_required
def dashboard_centro_operaciones(request):
    """
    🏢 Dashboard empresarial - Centro de Operaciones
    Vista principal que funciona como centro de control para suscriptores
    Incluye KPIs, reportes rápidos y navegación a todas las funciones
    """

    empresa = get_or_create_empresa(request)

    # 📅 Fechas de referencia
    hoy = date.today()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    inicio_mes = date(hoy.year, hoy.month, 1)

    inicio_mes_dt = inicio_mes_datetime(hoy)

    # --- FALLBACK DECIMAL PARA COALESCE ---
    ZERO_DEC = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))

    # 📊 KPIs PRINCIPALES (filtrados por empresa)

    # Documentos
    documentos_hoy = Documento.objects.filter(empresa=empresa, fecha_emision=hoy).count()
    documentos_semana = Documento.objects.filter(
        empresa=empresa, fecha_emision__gte=hace_7_dias
    ).count()
    documentos_mes = Documento.objects.filter(
        empresa=empresa, fecha_emision__gte=inicio_mes
    ).count()
    total_documentos = Documento.objects.filter(empresa=empresa).count()

    # --- BASES DE AGREGACIÓN ---
    base_hoy_fac = LineaServicio.objects.filter(
        documento__empresa=empresa, documento__fecha_emision=hoy, documento__tipo="FAC"
    )
    base_sem_fac = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_7_dias,
        documento__tipo="FAC",
    )
    base_mes_fac_srv = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=inicio_mes,
        documento__tipo="FAC",
    )
    base_mes_fac_rep = LineaRepuesto.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=inicio_mes,
        documento__tipo="FAC",
    )

    # --- FACTURACIÓN SEPARADA POR SERVICIOS Y REPUESTOS ---
    facturacion_servicios_hoy = total_servicios(base_hoy_fac)
    facturacion_servicios_semana = total_servicios(base_sem_fac)
    facturacion_servicios_mes = total_servicios(base_mes_fac_srv)

    # --- IVA: según regla, SOLO sobre repuestos (19% CL) ---
    total_repuestos_mes = total_repuestos(base_mes_fac_rep) or Decimal("0.00")
    iva_repuestos = Decimal("0.00")
    if empresa.pais == "CL":
        iva_repuestos = (total_repuestos_mes * Decimal("0.19")).quantize(Decimal("0.01"))

    # --- SUMA TOTAL DEL MES (sin IVA) ---
    facturacion_mes_total = (facturacion_servicios_mes or Decimal("0")) + (
        total_repuestos_mes or Decimal("0")
    )

    # Clientes
    clientes_activos = Cliente.objects.filter(empresa=empresa).count()

    # Clientes nuevos del mes (usando timezone correcto)
    now = timezone.now()
    clientes_nuevos_mes = Cliente.objects.filter(
        empresa=empresa,
        created_at__gte=inicio_mes_dt,
        created_at__lte=now,
    ).count()
    clientes_atendidos_semana = (
        Documento.objects.filter(empresa=empresa, fecha_emision__gte=hace_7_dias)
        .values("cliente")
        .distinct()
        .count()
    )

    # Técnicos y productividad
    tecnicos_activos = Tecnico.objects.filter(empresa=empresa, activo=True).count()

    # 📈 SERVICIOS MÁS DEMANDADOS (Top 5) - Usar solo cantidad por ahora
    servicios_top = (
        LineaServicio.objects.filter(
            documento__empresa=empresa, documento__fecha_emision__gte=hace_30_dias
        )
        .values("nombre")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")[:5]
    )

    # 🔧 TÉCNICOS MÁS PRODUCTIVOS (Top 5) - KPI por técnico efectivo

    # Técnico efectivo: Coalesce(linea.tecnico_responsable, documento__tecnico_responsable)
    tecnico_efectivo = Coalesce(F("tecnico_responsable"), F("documento__tecnico_responsable"))

    # Líneas del período (últimos 30 días, facturas)
    lineas_periodo = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_30_dias,
        documento__tipo="FAC",
    ).exclude(  # Excluir si ambos técnicos son nulos
        Q(tecnico_responsable__isnull=True) & Q(documento__tecnico_responsable__isnull=True)
    )

    # Agregación por técnico efectivo
    tecnicos_productivos_raw = (
        lineas_periodo.annotate(
            tecnico_id=tecnico_efectivo,
            ingresos_generados=Coalesce(Sum(SUBTOTAL_EXPR), ZERO_DEC),
            docs_realizados=Count("documento", distinct=True),
        )
        .values(
            "tecnico_id", "ingresos_generados", "docs_realizados"
        )  # Incluir todos los campos anotados
        .exclude(tecnico_id__isnull=True)
        .order_by("-ingresos_generados")[:5]
    )

    # Enriquecer con datos del técnico
    tecnicos_ids = [t["tecnico_id"] for t in tecnicos_productivos_raw]
    tecnicos_map = {
        t.id: t for t in Tecnico.objects.filter(id__in=tecnicos_ids).only("id", "nombre", "activo")
    }

    # Transformar a lista rica para el template
    tecnicos_productivos = [
        {
            "tecnico": tecnicos_map.get(row["tecnico_id"]),
            "ingresos_generados": row["ingresos_generados"],
            "docs_realizados": row["docs_realizados"],
        }
        for row in tecnicos_productivos_raw
    ]

    # 📋 ESTADO DE DOCUMENTOS
    presupuestos_pendientes = Documento.objects.filter(empresa=empresa, tipo="PRES").count()

    ordenes_en_proceso = Documento.objects.filter(empresa=empresa, tipo="OT").count()

    # Presupuestos del MES (mismo rango temporal que facturas)
    presupuestos_mes = Documento.objects.filter(
        empresa=empresa, tipo="PRES", fecha_emision__gte=inicio_mes
    ).count()

    facturas_mes = Documento.objects.filter(
        empresa=empresa, tipo="FAC", fecha_emision__gte=inicio_mes
    ).count()

    # 🚗 VEHÍCULOS Y MARCAS
    vehiculos_registrados = Vehiculo.objects.filter(empresa=empresa).count()
    marcas_atendidas = (
        Vehiculo.objects.filter(empresa=empresa).values("marca__nombre").distinct().count()
    )

    # ⚠️ ALERTAS Y OPORTUNIDADES
    alertas = []

    # Clientes inactivos (sin documentos en 60 días) - Solo clientes con documentos
    clientes_inactivos = (
        Cliente.objects.filter(empresa=empresa, documentos__isnull=False)
        .exclude(documentos__fecha_emision__gte=hoy - timedelta(days=60))
        .distinct()
        .count()
    )

    if clientes_inactivos > 0:
        alertas.append(
            {
                "tipo": "warning",
                "titulo": f"{clientes_inactivos} clientes inactivos",
                "descripcion": "No han visitado el taller en los últimos 60 días",
                "accion": "Enviar promoción de mantenimiento",
            }
        )

    # Presupuestos sin convertir (más de 15 días)
    presupuestos_antiguos = Documento.objects.filter(
        empresa=empresa, tipo="PRES", fecha_emision__lt=hoy - timedelta(days=15)
    ).count()

    if presupuestos_antiguos > 0:
        alertas.append(
            {
                "tipo": "info",
                "titulo": f"{presupuestos_antiguos} presupuestos antiguos",
                "descripcion": "Presupuestos de más de 15 días sin convertir",
                "accion": "Contactar clientes para seguimiento",
            }
        )

    # 📊 PREDICCIONES Y TENDENCIAS
    if documentos_mes > 0:
        dias_transcurridos = (hoy - inicio_mes).days + 1
        proyeccion_docs_mes = (documentos_mes / dias_transcurridos) * 30
        proyeccion_facturacion = (
            (facturacion_mes_total / dias_transcurridos) * 30 if facturacion_mes_total > 0 else 0
        )
    else:
        proyeccion_docs_mes = 0
        proyeccion_facturacion = 0

    # 💰 CÁLCULO TICKET PROMEDIO - Coherente con el numerador
    # Opción 1: ticket de facturas del mes, servicios + repuestos
    lineas_fac_mes_srv = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__tipo="FAC",
        documento__fecha_emision__gte=inicio_mes,
    )
    lineas_fac_mes_rep = LineaRepuesto.objects.filter(
        documento__empresa=empresa,
        documento__tipo="FAC",
        documento__fecha_emision__gte=inicio_mes,
    )

    monto_fac_mes = Coalesce(
        lineas_fac_mes_srv.aggregate(t=Sum(SUBTOTAL_EXPR))["t"], Decimal("0")
    ) + Coalesce(lineas_fac_mes_rep.aggregate(t=Sum(SUBTOTAL_EXPR))["t"], Decimal("0"))

    ticket_promedio = (monto_fac_mes / facturas_mes) if facturas_mes else Decimal("0")

    # 🎯 MÉTRICAS DE EFICIENCIA
    eficiencia_conversion = (facturas_mes / max(presupuestos_mes + facturas_mes, 1)) * 100

    # 📋 CHECKLIST DE ONBOARDING
    checklist_onboarding = {
        "empresa_configurada": bool(
            empresa.nombre_taller
            and empresa.pais
            and empresa.moneda
            and hasattr(empresa, "config")
            and empresa.config.tasa_impuesto is not None
        ),
        "tecnico_creado": tecnicos_activos > 0,
        "cliente_creado": clientes_activos > 0,
        "vehiculo_creado": vehiculos_registrados > 0,
        "documento_creado": total_documentos > 0,
    }
    checklist_completo = all(checklist_onboarding.values())

    context = {
        # Información de empresa
        "empresa": empresa,
        "pais_emoji": {"CL": "🇨🇱", "US": "🇺🇸", "MX": "🇲🇽"}.get(empresa.pais, "🌎"),
        "moneda": empresa.simbolo_moneda,
        # KPIs principales
        "documentos_hoy": documentos_hoy,
        "documentos_semana": documentos_semana,
        "documentos_mes": documentos_mes,
        "total_documentos": total_documentos,
        "facturacion_servicios_hoy": facturacion_servicios_hoy,
        "facturacion_servicios_semana": facturacion_servicios_semana,
        "facturacion_servicios_mes": facturacion_servicios_mes,
        "facturacion_mes_total": facturacion_mes_total,
        "total_repuestos_mes": total_repuestos_mes,
        "iva_repuestos": iva_repuestos,
        "clientes_activos": clientes_activos,
        "clientes_nuevos_mes": clientes_nuevos_mes,
        "clientes_atendidos_semana": clientes_atendidos_semana,
        "tecnicos_activos": tecnicos_activos,
        "vehiculos_registrados": vehiculos_registrados,
        "marcas_atendidas": marcas_atendidas,
        # Rankings y tops
        "servicios_top": servicios_top,
        "tecnicos_productivos": tecnicos_productivos,
        # Estado operativo
        "presupuestos_pendientes": presupuestos_pendientes,
        "presupuestos_mes": presupuestos_mes,
        "ordenes_en_proceso": ordenes_en_proceso,
        "facturas_mes": facturas_mes,
        # Alertas
        "alertas": alertas,
        "clientes_inactivos": clientes_inactivos,
        # Proyecciones
        "proyeccion_docs_mes": int(proyeccion_docs_mes),
        "proyeccion_facturacion": proyeccion_facturacion,
        "ticket_promedio": ticket_promedio,
        "eficiencia_conversion": eficiencia_conversion,
        # Checklist de onboarding
        "checklist_onboarding": checklist_onboarding,
        "checklist_completo": checklist_completo,
        # Fechas
        "fecha_hoy": hoy,
        "mes_actual": hoy.strftime("%B %Y"),
    }

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "dashboard/centro_operaciones.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(request, template_name, context)


@country_login_required
def dashboard_centro_operaciones_espacial(request):
    """
    Dashboard especializado con estética espacial futurista
    Usa exactamente la misma lógica de datos que dashboard_centro_operaciones
    Solo cambia el template al final para usar el diseño espacial
    """
    # El idioma ya está establecido por LanguagePolicyMiddleware
    # No forzar ningún idioma aquí, respetar la preferencia del usuario

    empresa = get_or_create_empresa(request)

    # 📅 Fechas de referencia (MISMA LÓGICA QUE dashboard_centro_operaciones)
    hoy = date.today()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    inicio_mes = date(hoy.year, hoy.month, 1)

    inicio_mes_dt = inicio_mes_datetime(hoy)

    # --- FALLBACK DECIMAL PARA COALESCE ---
    ZERO_DEC = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))

    # 📊 KPIs PRINCIPALES (MISMA LÓGICA)
    documentos_hoy = Documento.objects.filter(empresa=empresa, fecha_emision=hoy).count()
    documentos_semana = Documento.objects.filter(
        empresa=empresa, fecha_emision__gte=hace_7_dias
    ).count()
    documentos_mes = Documento.objects.filter(
        empresa=empresa, fecha_emision__gte=inicio_mes
    ).count()
    total_documentos = Documento.objects.filter(empresa=empresa).count()

    # --- BASES DE AGREGACIÓN ---
    base_hoy_fac = LineaServicio.objects.filter(
        documento__empresa=empresa, documento__fecha_emision=hoy, documento__tipo="FAC"
    )
    base_sem_fac = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_7_dias,
        documento__tipo="FAC",
    )
    base_mes_fac_srv = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=inicio_mes,
        documento__tipo="FAC",
    )
    base_mes_fac_rep = LineaRepuesto.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=inicio_mes,
        documento__tipo="FAC",
    )

    # --- FACTURACIÓN SEPARADA POR SERVICIOS Y REPUESTOS ---
    facturacion_servicios_hoy = total_servicios(base_hoy_fac)
    facturacion_servicios_semana = total_servicios(base_sem_fac)
    facturacion_servicios_mes = total_servicios(base_mes_fac_srv)

    # --- IVA: según regla, SOLO sobre repuestos (19% CL) ---
    total_repuestos_mes = total_repuestos(base_mes_fac_rep) or Decimal("0.00")
    iva_repuestos = Decimal("0.00")
    if empresa.pais == "CL":
        iva_repuestos = (total_repuestos_mes * Decimal("0.19")).quantize(Decimal("0.01"))

    # --- SUMA TOTAL DEL MES (sin IVA) ---
    facturacion_mes_total = (facturacion_servicios_mes or Decimal("0")) + (
        total_repuestos_mes or Decimal("0")
    )

    # Clientes
    clientes_activos = Cliente.objects.filter(empresa=empresa).count()
    now = timezone.now()
    clientes_nuevos_mes = Cliente.objects.filter(
        empresa=empresa,
        created_at__gte=inicio_mes_dt,
        created_at__lte=now,
    ).count()
    clientes_atendidos_semana = (
        Documento.objects.filter(empresa=empresa, fecha_emision__gte=hace_7_dias)
        .values("cliente")
        .distinct()
        .count()
    )

    # Técnicos y productividad
    tecnicos_activos = Tecnico.objects.filter(empresa=empresa, activo=True).count()

    # 📈 SERVICIOS MÁS DEMANDADOS (Top 5)
    servicios_top = (
        LineaServicio.objects.filter(
            documento__empresa=empresa, documento__fecha_emision__gte=hace_30_dias
        )
        .values("nombre")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")[:5]
    )

    # 🔧 TÉCNICOS MÁS PRODUCTIVOS (Top 5)
    tecnico_efectivo = Coalesce(F("tecnico_responsable"), F("documento__tecnico_responsable"))
    lineas_periodo = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_30_dias,
        documento__tipo="FAC",
    ).exclude(Q(tecnico_responsable__isnull=True) & Q(documento__tecnico_responsable__isnull=True))

    tecnicos_productivos_raw = (
        lineas_periodo.annotate(
            tecnico_id=tecnico_efectivo,
            ingresos_generados=Coalesce(Sum(SUBTOTAL_EXPR), ZERO_DEC),
            docs_realizados=Count("documento", distinct=True),
        )
        .values("tecnico_id", "ingresos_generados", "docs_realizados")
        .exclude(tecnico_id__isnull=True)
        .order_by("-ingresos_generados")[:5]
    )

    tecnicos_ids = [t["tecnico_id"] for t in tecnicos_productivos_raw]
    tecnicos_map = {
        t.id: t for t in Tecnico.objects.filter(id__in=tecnicos_ids).only("id", "nombre", "activo")
    }

    tecnicos_productivos = [
        {
            "tecnico": tecnicos_map.get(row["tecnico_id"]),
            "ingresos_generados": row["ingresos_generados"],
            "docs_realizados": row["docs_realizados"],
        }
        for row in tecnicos_productivos_raw
    ]

    # 📋 ESTADO DE DOCUMENTOS
    presupuestos_pendientes = Documento.objects.filter(empresa=empresa, tipo="PRES").count()
    ordenes_en_proceso = Documento.objects.filter(empresa=empresa, tipo="OT").count()
    presupuestos_mes = Documento.objects.filter(
        empresa=empresa, tipo="PRES", fecha_emision__gte=inicio_mes
    ).count()
    facturas_mes = Documento.objects.filter(
        empresa=empresa, tipo="FAC", fecha_emision__gte=inicio_mes
    ).count()

    # 🚗 VEHÍCULOS Y MARCAS
    vehiculos_registrados = Vehiculo.objects.filter(empresa=empresa).count()
    marcas_atendidas = (
        Vehiculo.objects.filter(empresa=empresa).values("marca__nombre").distinct().count()
    )

    # ⚠️ ALERTAS Y OPORTUNIDADES
    alertas = []
    clientes_inactivos = (
        Cliente.objects.filter(empresa=empresa, documentos__isnull=False)
        .exclude(documentos__fecha_emision__gte=hoy - timedelta(days=60))
        .distinct()
        .count()
    )

    if clientes_inactivos > 0:
        alertas.append(
            {
                "tipo": "warning",
                "titulo": f"{clientes_inactivos} clientes inactivos",
                "descripcion": "No han visitado el taller en los últimos 60 días",
                "accion": "Enviar promoción de mantenimiento",
            }
        )

    presupuestos_antiguos = Documento.objects.filter(
        empresa=empresa, tipo="PRES", fecha_emision__lt=hoy - timedelta(days=15)
    ).count()

    if presupuestos_antiguos > 0:
        alertas.append(
            {
                "tipo": "info",
                "titulo": f"{presupuestos_antiguos} presupuestos antiguos",
                "descripcion": "Presupuestos de más de 15 días sin convertir",
                "accion": "Contactar clientes para seguimiento",
            }
        )

    # 📊 PREDICCIONES Y TENDENCIAS
    if documentos_mes > 0:
        dias_transcurridos = (hoy - inicio_mes).days + 1
        proyeccion_docs_mes = (documentos_mes / dias_transcurridos) * 30
        proyeccion_facturacion = (
            (facturacion_mes_total / dias_transcurridos) * 30 if facturacion_mes_total > 0 else 0
        )
    else:
        proyeccion_docs_mes = 0
        proyeccion_facturacion = 0

    # 💰 CÁLCULO TICKET PROMEDIO
    lineas_fac_mes_srv = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__tipo="FAC",
        documento__fecha_emision__gte=inicio_mes,
    )
    lineas_fac_mes_rep = LineaRepuesto.objects.filter(
        documento__empresa=empresa,
        documento__tipo="FAC",
        documento__fecha_emision__gte=inicio_mes,
    )

    monto_fac_mes = Coalesce(
        lineas_fac_mes_srv.aggregate(t=Sum(SUBTOTAL_EXPR))["t"], Decimal("0")
    ) + Coalesce(lineas_fac_mes_rep.aggregate(t=Sum(SUBTOTAL_EXPR))["t"], Decimal("0"))

    ticket_promedio = (monto_fac_mes / facturas_mes) if facturas_mes else Decimal("0")

    # 🎯 MÉTRICAS DE EFICIENCIA
    eficiencia_conversion = (facturas_mes / max(presupuestos_mes + facturas_mes, 1)) * 100

    # 📊 DATOS PARA GRÁFICOS (DATOS REALES)
    import json
    from calendar import month_abbr

    # 1. Gráfico de Ingresos Mensuales (últimos 7 meses)
    ingresos_mensuales_labels = []
    ingresos_mensuales_data = []
    for i in range(6, -1, -1):  # Últimos 7 meses (del más antiguo al más reciente)
        # Calcular el mes retrocediendo correctamente
        mes_actual = hoy.month
        año_actual = hoy.year

        # Retroceder i meses
        meses_retroceder = i
        if mes_actual > meses_retroceder:
            mes_target = mes_actual - meses_retroceder
            año_target = año_actual
        else:
            meses_restantes = meses_retroceder - mes_actual
            mes_target = 12 - (meses_restantes % 12)
            if mes_target == 0:
                mes_target = 12
            año_target = año_actual - (1 + meses_restantes // 12)

        inicio_mes = date(año_target, mes_target, 1)
        if mes_target == 12:
            fin_mes = date(año_target + 1, 1, 1)
        else:
            fin_mes = date(año_target, mes_target + 1, 1)

        # Calcular facturación del mes (servicios + repuestos)
        facturacion_mes_srv = total_servicios(
            LineaServicio.objects.filter(
                documento__empresa=empresa,
                documento__tipo="FAC",
                documento__fecha_emision__gte=inicio_mes,
                documento__fecha_emision__lt=fin_mes,
            )
        ) or Decimal("0")

        facturacion_mes_rep = total_repuestos(
            LineaRepuesto.objects.filter(
                documento__empresa=empresa,
                documento__tipo="FAC",
                documento__fecha_emision__gte=inicio_mes,
                documento__fecha_emision__lt=fin_mes,
            )
        ) or Decimal("0")

        total_mes = float(facturacion_mes_srv + facturacion_mes_rep)
        ingresos_mensuales_labels.append(month_abbr[inicio_mes.month].upper())
        ingresos_mensuales_data.append(total_mes)

    # 2. Gráfico de Servicios (distribución porcentual de los top servicios)
    servicios_chart_labels = []
    servicios_chart_data = []
    servicios_chart_colors = ["#00ffff", "#8a2be2", "#ffd700", "#00ff88", "#ff3b3b"]

    if servicios_top:
        total_servicios_count = sum(s["cantidad"] for s in servicios_top)
        for idx, servicio in enumerate(servicios_top[:5]):  # Top 5
            servicios_chart_labels.append(servicio["nombre"][:20])  # Limitar longitud
            porcentaje = (
                (servicio["cantidad"] / total_servicios_count * 100)
                if total_servicios_count > 0
                else 0
            )
            servicios_chart_data.append(round(porcentaje, 1))
    else:
        # Si no hay datos, mostrar mensaje vacío
        servicios_chart_labels = []
        servicios_chart_data = []

    # 3. Gráfico de Técnicos Productivos (barras con ingresos generados)
    tecnicos_chart_labels = []
    tecnicos_chart_data = []

    if tecnicos_productivos:
        for tecnico in tecnicos_productivos[:4]:  # Top 4 técnicos
            nombre = tecnico["tecnico"].nombre if tecnico["tecnico"] else "Unknown"
            tecnicos_chart_labels.append(nombre[:15])  # Limitar longitud
            # Calcular porcentaje de productividad basado en ingresos (normalizado)
            ingresos = float(tecnico["ingresos_generados"] or 0)
            # Si hay ingresos, calcular un porcentaje relativo (máximo 100%)
            if ingresos > 0 and tecnicos_productivos:
                max_ingresos = max(
                    float(t["ingresos_generados"] or 0) for t in tecnicos_productivos
                )
                porcentaje = (ingresos / max_ingresos * 100) if max_ingresos > 0 else 0
            else:
                porcentaje = 0
            tecnicos_chart_data.append(round(porcentaje, 1))
    else:
        # Si no hay datos, mostrar mensaje vacío
        tecnicos_chart_labels = []
        tecnicos_chart_data = []

    # Convertir a JSON para pasar al template
    chart_data_json = json.dumps(
        {
            "ingresos_mensuales": {
                "labels": ingresos_mensuales_labels,
                "data": ingresos_mensuales_data,
            },
            "servicios": {
                "labels": servicios_chart_labels,
                "data": servicios_chart_data,
            },
            "tecnicos": {
                "labels": tecnicos_chart_labels,
                "data": tecnicos_chart_data,
            },
        }
    )

    from taller.services.branding_service import BrandingService

    brand = BrandingService.get_brand(empresa, user=request.user)
    brand_dict = brand.as_dict()

    context = {
        # Información de empresa
        "empresa": empresa,
        "pais_emoji": {"CL": "🇨🇱", "US": "🇺🇸", "MX": "🇲🇽"}.get(empresa.pais, "🌎"),
        "moneda": empresa.simbolo_moneda,
        # KPIs principales
        "documentos_hoy": documentos_hoy,
        "documentos_semana": documentos_semana,
        "documentos_mes": documentos_mes,
        "total_documentos": total_documentos,
        "facturacion_servicios_hoy": facturacion_servicios_hoy,
        "facturacion_servicios_semana": facturacion_servicios_semana,
        "facturacion_servicios_mes": facturacion_servicios_mes,
        "facturacion_mes_total": facturacion_mes_total,
        "total_repuestos_mes": total_repuestos_mes,
        "iva_repuestos": iva_repuestos,
        "clientes_activos": clientes_activos,
        "clientes_nuevos_mes": clientes_nuevos_mes,
        "clientes_atendidos_semana": clientes_atendidos_semana,
        "tecnicos_activos": tecnicos_activos,
        "vehiculos_registrados": vehiculos_registrados,
        "marcas_atendidas": marcas_atendidas,
        # Rankings y tops
        "servicios_top": servicios_top,
        "tecnicos_productivos": tecnicos_productivos,
        # Estado operativo
        "presupuestos_pendientes": presupuestos_pendientes,
        "presupuestos_mes": presupuestos_mes,
        "ordenes_en_proceso": ordenes_en_proceso,
        "facturas_mes": facturas_mes,
        # Alertas
        "alertas": alertas,
        "clientes_inactivos": clientes_inactivos,
        # Proyecciones
        "proyeccion_docs_mes": int(proyeccion_docs_mes),
        "proyeccion_facturacion": proyeccion_facturacion,
        "ticket_promedio": ticket_promedio,
        "eficiencia_conversion": eficiencia_conversion,
        # Fechas
        "fecha_hoy": hoy,
        "mes_actual": hoy.strftime("%B %Y"),
        # Branding — fuente única de verdad via BrandingService
        "BRAND": brand_dict,
        "company_name": brand_dict["name"],
        "company_logo_url": brand_dict["logo_url"],
        "company_color": brand_dict["primary_color"],
        "company_tagline": brand_dict["tagline"],
        "es_dashboard_espacial": True,
        # Datos para gráficos (JSON)
        "chart_data_json": chart_data_json,
    }

    # Usar template resolution unificado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language
    from taller.utils.templates import select_country_lang_template

    # Seleccionar template espacial
    # Para USA, siempre usar el template de USA (soporta inglés y español)
    if hasattr(empresa, "pais") and empresa.pais == "US":
        template_name = "us/en/dashboard/centro_operaciones_espacial.html"
        context["use_usa_base"] = True
    elif request.path.startswith("/us/"):
        # Para rutas /us/, siempre usar template de USA (tiene traducciones)
        template_name = "us/en/dashboard/centro_operaciones_espacial.html"
        context["use_usa_base"] = True
    else:
        template_name = select_country_lang_template(
            "dashboard/centro_operaciones_espacial.html",
            getattr(empresa, "pais", "cl").lower(),
            get_language(),
        )

    return TemplateResponse(request, template_name, context)
