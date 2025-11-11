from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import redirect
from django.utils import timezone

from taller.auth.decorators import login_required_default
from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo

# --- CONSTANTS ---
SUBTOTAL_EXPR = ExpressionWrapper(
    F("precio_unitario") * F("cantidad"),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)

ZERO_DEC = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


# --- HELPER FUNCTIONS ---
def total_servicios(qs_base):
    """Calcula el total de servicios usando subtotal (precio * cantidad)"""
    return qs_base.aggregate(total=Coalesce(Sum(SUBTOTAL_EXPR), ZERO_DEC))["total"]


def total_repuestos(qs_base):
    """Calcula el total de repuestos usando subtotal (precio * cantidad)"""
    return qs_base.aggregate(total=Coalesce(Sum(SUBTOTAL_EXPR), ZERO_DEC))["total"]


@login_required_default
def dashboard_centro_operaciones(request):
    """
    🏢 Dashboard empresarial - Centro de Operaciones
    Vista principal que funciona como centro de control para suscriptores
    Incluye KPIs, reportes rápidos y navegación a todas las funciones
    """

    # 🔒 Obtener empresa del usuario logueado - NO crear silenciosamente
    try:
        empresa = request.user.empresa
    except Exception:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")

        # Detectar país y redirigir al namespace correcto
        if "/us/" in request.path:
            return redirect("usa:configuracion")
        elif "/cl/" in request.path:
            return redirect("chile:configuracion")
        else:
            # Fallback al namespace global
            return redirect("configuracion")

    # 📅 Fechas de referencia
    hoy = timezone.localdate()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    inicio_mes = date(hoy.year, hoy.month, 1)

    # Zona horaria para clientes nuevos del mes
    tz = timezone.get_current_timezone()
    # Corregir para zoneinfo (Python 3.9+) que no tiene localize()
    if hasattr(tz, "localize"):
        inicio_mes_dt = tz.localize(datetime(hoy.year, hoy.month, 1, 0, 0, 0))
    else:
        # Para zoneinfo, usar datetime con tzinfo directamente
        inicio_mes_dt = datetime(hoy.year, hoy.month, 1, 0, 0, 0, tzinfo=tz)

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

    context = {
        # Información de empresa
        "empresa": empresa,
        "pais_emoji": "🇨🇱" if empresa.pais == "CL" else "🇺🇸",
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
    }

    # Usar template resolution en lugar de template hardcodeado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    template_name = select_country_lang_template(
        "dashboard/centro_operaciones.html",
        getattr(request.user.empresa, "pais", "cl").lower(),
        get_language(),
    )

    return TemplateResponse(request, template_name, context)


@login_required_default
def dashboard_centro_operaciones_espacial(request):
    """
    Dashboard especializado con estética espacial futurista
    """
    # Inicializar contexto
    contexto = {}

    # Forzar idioma inglés para URLs de USA
    if request.path.startswith("/us/"):
        from django.utils import translation

        translation.activate("en")
        request.LANGUAGE_CODE = "en"
        # Forzar contexto de idioma
        contexto["LANGUAGE_CODE"] = "en"
        contexto["LANGUAGE_NAME"] = "English"

    # Obtener empresa del usuario autenticado - NO crear silenciosamente
    try:
        empresa = request.user.empresa
    except Exception:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        # Detectar país y redirigir al namespace correcto
        if "/us/" in request.path:
            return redirect("usa:configuracion")
        elif "/cl/" in request.path:
            return redirect("chile:configuracion")
        else:
            # Fallback al namespace global
            return redirect("configuracion")

    # --- EXPRESIÓN DE SUBTOTAL POR LÍNEA ---
    line_subtotal = ExpressionWrapper(
        F("precio_unitario") * F("cantidad"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    # --- FALLBACK DECIMAL PARA COALESCE ---
    ZERO_DEC = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))

    # Datos básicos y seguros
    documentos_total = Documento.objects.filter(empresa=empresa).count()
    clientes_total = Cliente.objects.filter(empresa=empresa).count()
    tecnicos_total = Tecnico.objects.filter(empresa=empresa).count()

    # Documentos recientes (últimos 30 días)
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    documentos_mes = Documento.objects.filter(
        empresa=empresa, fecha_emision__gte=hace_30_dias
    ).count()

    # Facturación mensual simplificada
    facturacion_mes = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_30_dias,
        documento__tipo="FAC",
    ).aggregate(total=Coalesce(Sum(line_subtotal), ZERO_DEC))["total"]

    # Ticket promedio
    ticket_promedio = facturacion_mes / documentos_mes if documentos_mes > 0 else Decimal("0")

    # Documentos por tipo (simplificado)
    presupuestos = Documento.objects.filter(empresa=empresa, tipo="PRES").count()
    facturas = Documento.objects.filter(empresa=empresa, tipo="FAC").count()
    ordenes = Documento.objects.filter(empresa=empresa, tipo="OT").count()

    # Branding: preferir ConfiguracionEmpresa si existe (igual que context processor unificado)
    from taller.models.configuracion import ConfiguracionEmpresa

    conf = ConfiguracionEmpresa.objects.filter(empresa=empresa).first()
    logo_url = None
    tagline = None
    if conf:
        if getattr(conf, "logo", None):
            try:
                logo_url = conf.logo.url
            except Exception:
                logo_url = None
        if hasattr(conf, "tagline") and conf.tagline:
            tagline = conf.tagline
    # Fallbacks si no hay config
    if not logo_url:
        logo_url = empresa.logo.url if getattr(empresa, "logo", None) else None
    if not tagline:
        tagline = getattr(empresa, "tagline", None)

    contexto.update(
        {
            "empresa": empresa,
            "documentos_total": documentos_total,
            "documentos_mes": documentos_mes,
            "clientes_total": clientes_total,
            "tecnicos_total": tecnicos_total,
            "facturacion_mes": facturacion_mes,
            "ticket_promedio": ticket_promedio,
            "presupuestos": presupuestos,
            "facturas": facturas,
            "ordenes": ordenes,
            "es_dashboard_espacial": True,
            # Variables para el template base
            "company_name": empresa.nombre_taller,
            "company_logo_url": logo_url,
            "company_color": (
                empresa.color_primario if hasattr(empresa, "color_primario") else "#00ffff"
            ),
            "company_tagline": tagline,
        }
    )

    # --- Asegurar compatibilidad con el sistema de BRAND ---
    # Algunos includes y templates leen BRAND.* (p.ej. templates/_includes/brand_header.html)
    # Para evitar inconsistencias (BRAND distinto a company_*), exponemos un objeto BRAND
    # construido a partir de la empresa actual. Esto garantiza que tanto variables
    # company_* como BRAND.* apunten a la misma marca en la misma petición.
    try:
        brand_obj = {
            "logo_url": contexto.get("company_logo_url"),
            "name": contexto.get("company_name"),
            "tagline": contexto.get("company_tagline"),
            "primary_color": contexto.get("company_color"),
            "secondary_color": contexto.get("company_color"),
            "country": getattr(empresa, "pais", None),
            "currency": getattr(empresa, "simbolo_moneda", None),
        }
        contexto["BRAND"] = brand_obj
    except Exception:
        # No bloquear la vista por problemas menores al construir BRAND
        pass

    # Usar template resolution unificado
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.utils.templates import select_country_lang_template

    # Forzar template correcto basado en la URL y idioma
    # Verificar si el usuario tiene empresa de USA
    if hasattr(empresa, "pais") and empresa.pais == "US":
        # Usuario de USA - usar template específico de USA
        template_name = "taller/us/en/dashboard/centro_operaciones_espacial.html"
        contexto["use_usa_base"] = True
        print(f"[DEBUG] Using USA template for user {request.user.username}")
    elif request.path.startswith("/us/"):
        # Para USA, usar template en inglés por defecto, pero permitir español
        if get_language() == "es":
            # Si se selecciona español, usar template de Chile
            template_name = "taller/cl/es/dashboard/centro_operaciones_espacial.html"
        else:
            # Por defecto inglés para USA - usar template que extiende base en inglés
            template_name = "taller/us/en/dashboard/centro_operaciones_espacial.html"
            # Forzar que use el template base en inglés
            contexto["use_usa_base"] = True
    else:
        template_name = select_country_lang_template(
            "dashboard/centro_operaciones_espacial.html",
            getattr(empresa, "pais", "cl").lower(),
            get_language(),
        )

    return TemplateResponse(request, template_name, contexto)
