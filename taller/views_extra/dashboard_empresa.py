
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaServicio
from taller.models.empresa import Empresa
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo


@login_required
def dashboard_centro_operaciones(request):
    """
    🏢 Dashboard empresarial - Centro de Operaciones
    Vista principal que funciona como centro de control para suscriptores
    Incluye KPIs, reportes rápidos y navegación a todas las funciones
    """
    
    # 🔒 Obtener empresa del usuario logueado
    try:
        empresa = request.user.empresa
    except:
        # Si no tiene empresa, crear una básica o redirigir
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    # 📅 Fechas de referencia
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    inicio_mes = hoy.replace(day=1)
    
    # 📊 KPIs PRINCIPALES (filtrados por empresa)
    
    # Documentos
    documentos_hoy = Documento.objects.filter(empresa=empresa, fecha_emision=hoy).count()
    documentos_semana = Documento.objects.filter(empresa=empresa, fecha_emision__gte=hace_7_dias).count()
    documentos_mes = Documento.objects.filter(empresa=empresa, fecha_emision__gte=inicio_mes).count()
    total_documentos = Documento.objects.filter(empresa=empresa).count()
    
    # Facturación (basada en servicios)
    facturacion_hoy = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision=hoy,
        documento__tipo='FAC'
    ).aggregate(total=Sum(F('precio_unitario') * F('cantidad')))['total'] or 0
    
    facturacion_semana = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_7_dias,
        documento__tipo='FAC'
    ).aggregate(total=Sum(F('precio_unitario') * F('cantidad')))['total'] or 0
    
    facturacion_mes = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=inicio_mes,
        documento__tipo='FAC'
    ).aggregate(total=Sum(F('precio_unitario') * F('cantidad')))['total'] or 0
    
    # Clientes
    clientes_activos = Cliente.objects.filter(empresa=empresa, activo=True).count()
    clientes_nuevos_mes = Cliente.objects.filter(empresa=empresa, fecha_creacion__gte=inicio_mes).count()
    clientes_atendidos_semana = Documento.objects.filter(
        empresa=empresa, 
        fecha_emision__gte=hace_7_dias
    ).values('cliente').distinct().count()
    
    # Técnicos y productividad
    tecnicos_activos = Tecnico.objects.filter(empresa=empresa, activo=True).count()
    
    # 📈 SERVICIOS MÁS DEMANDADOS (Top 5)
    servicios_top = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_30_dias
    ).values('nombre').annotate(
        cantidad=Count('id'),
        ingresos=Sum(F('precio_unitario') * F('cantidad'))
    ).order_by('-cantidad')[:5]
    
    # 🔧 TÉCNICOS MÁS PRODUCTIVOS (Top 5)
    tecnicos_productivos = Tecnico.objects.filter(empresa=empresa, activo=True).annotate(
    docs_realizados=Count('documentos', filter=Q(documentos__fecha_emision__gte=hace_30_dias)),
    ingresos_generados=Sum('documentos__lineas_servicio__precio_unitario', filter=Q(documentos__fecha_emision__gte=hace_30_dias))
    ).order_by('-docs_realizados')[:5]
    
    # 📋 ESTADO DE DOCUMENTOS
    presupuestos_pendientes = Documento.objects.filter(
        empresa=empresa,
        tipo='PRES'
    ).count()
    
    ordenes_en_proceso = Documento.objects.filter(
        empresa=empresa,
        tipo='OT'
    ).count()
    
    facturas_mes = Documento.objects.filter(
        empresa=empresa,
        tipo='FAC',
        fecha_emision__gte=inicio_mes
    ).count()
    
    # 🚗 VEHÍCULOS Y MARCAS
    vehiculos_registrados = Vehiculo.objects.filter(empresa=empresa).count()
    marcas_atendidas = Vehiculo.objects.filter(empresa=empresa).values('marca__nombre').distinct().count()
    
    # ⚠️ ALERTAS Y OPORTUNIDADES
    alertas = []
    
    # Clientes inactivos (sin documentos en 60 días)
    clientes_inactivos = Cliente.objects.filter(
        empresa=empresa,
        activo=True
    ).exclude(
        documentos__fecha_emision__gte=hoy - timedelta(days=60)
    ).count()
    
    if clientes_inactivos > 0:
        alertas.append({
            'tipo': 'warning',
            'titulo': f'{clientes_inactivos} clientes inactivos',
            'descripcion': 'No han visitado el taller en los últimos 60 días',
            'accion': 'Enviar promoción de mantenimiento'
        })
    
    # Presupuestos sin convertir (más de 15 días)
    presupuestos_antiguos = Documento.objects.filter(
        empresa=empresa,
        tipo='PRES',
        fecha_emision__lt=hoy - timedelta(days=15)
    ).count()
    
    if presupuestos_antiguos > 0:
        alertas.append({
            'tipo': 'info',
            'titulo': f'{presupuestos_antiguos} presupuestos antiguos',
            'descripcion': 'Presupuestos de más de 15 días sin convertir',
            'accion': 'Contactar clientes para seguimiento'
        })
    
    # 📊 PREDICCIONES Y TENDENCIAS
    if documentos_mes > 0:
        dias_transcurridos = (hoy - inicio_mes).days + 1
        proyeccion_docs_mes = (documentos_mes / dias_transcurridos) * 30
        proyeccion_facturacion = (facturacion_mes / dias_transcurridos) * 30 if facturacion_mes > 0 else 0
    else:
        proyeccion_docs_mes = 0
        proyeccion_facturacion = 0
    
    # 💰 CÁLCULO TICKET PROMEDIO
    ticket_promedio = facturacion_mes / max(facturas_mes, 1)
    
    # 🎯 MÉTRICAS DE EFICIENCIA
    eficiencia_conversion = (facturas_mes / max(presupuestos_pendientes + facturas_mes, 1)) * 100
    
    context = {
        # Información de empresa
        'empresa': empresa,
        'pais_emoji': '🇨🇱' if empresa.pais == 'CL' else '🇺🇸',
        'moneda': empresa.simbolo_moneda,
        
        # KPIs principales
        'documentos_hoy': documentos_hoy,
        'documentos_semana': documentos_semana,
        'documentos_mes': documentos_mes,
        'total_documentos': total_documentos,
        
        'facturacion_hoy': facturacion_hoy,
        'facturacion_semana': facturacion_semana,
        'facturacion_mes': facturacion_mes,
        
        'clientes_activos': clientes_activos,
        'clientes_nuevos_mes': clientes_nuevos_mes,
        'clientes_atendidos_semana': clientes_atendidos_semana,
        
        'tecnicos_activos': tecnicos_activos,
        'vehiculos_registrados': vehiculos_registrados,
        'marcas_atendidas': marcas_atendidas,
        
        # Rankings y tops
        'servicios_top': servicios_top,
        'tecnicos_productivos': tecnicos_productivos,
        
        # Estado operativo
        'presupuestos_pendientes': presupuestos_pendientes,
        'ordenes_en_proceso': ordenes_en_proceso,
        'facturas_mes': facturas_mes,
        
        # Alertas
        'alertas': alertas,
        'clientes_inactivos': clientes_inactivos,
        
        # Proyecciones
        'proyeccion_docs_mes': int(proyeccion_docs_mes),
        'proyeccion_facturacion': proyeccion_facturacion,
        'ticket_promedio': ticket_promedio,
        'eficiencia_conversion': eficiencia_conversion,
        
        # Fechas
        'fecha_hoy': hoy,
        'mes_actual': hoy.strftime('%B %Y'),
    }
    
    # Usar template resolution en lugar de template hardcodeado
    from taller.utils.templates import select_country_lang_template
    from django.utils.translation import get_language
    from django.template.response import TemplateResponse
    
    template_name = select_country_lang_template(
        "dashboard/centro_operaciones.html", 
        getattr(request.user.empresa, 'pais', 'cl').lower(), 
        get_language()
    )
    
    return render(request, template_name, context)


@login_required
@login_required
def dashboard_centro_operaciones_espacial(request):
    """
    Dashboard especializado con estética espacial futurista
    """
    # Obtener empresa del usuario autenticado
    try:
        empresa = Empresa.objects.get(user=request.user)
    except Empresa.DoesNotExist:
        messages.error(request, "No se encontró una empresa asociada a este usuario.")
        return redirect('login')
    
    # Datos básicos y seguros
    documentos_total = Documento.objects.filter(empresa=empresa).count()
    clientes_total = Cliente.objects.filter(empresa=empresa).count()
    tecnicos_total = Tecnico.objects.filter(empresa=empresa).count()
    
    # Documentos recientes (últimos 30 días)
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    documentos_mes = Documento.objects.filter(empresa=empresa, fecha_emision__gte=hace_30_dias).count()
    
    # Facturación mensual simplificada
    facturacion_mes = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_30_dias,
        documento__tipo='FAC'
    ).aggregate(total=Sum(F('precio_unitario') * F('cantidad')))['total'] or Decimal('0')
    
    # Ticket promedio
    ticket_promedio = facturacion_mes / documentos_mes if documentos_mes > 0 else Decimal('0')
    
    # Documentos por tipo (simplificado)
    presupuestos = Documento.objects.filter(empresa=empresa, tipo='PRES').count()
    facturas = Documento.objects.filter(empresa=empresa, tipo='FAC').count()
    ordenes = Documento.objects.filter(empresa=empresa, tipo='OT').count()
    
    # 📊 DATOS PARA GRÁFICOS REALES
    
    # 1. Ingresos por mes (últimos 7 meses)
    ingresos_por_mes = []
    labels_meses = []
    for i in range(6, -1, -1):  # Últimos 7 meses
        fecha_inicio = hoy - timedelta(days=30*i)
        fecha_fin = fecha_inicio + timedelta(days=30)
        
        ingresos_mes = LineaServicio.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__gte=fecha_inicio,
            documento__fecha_emision__lt=fecha_fin,
            documento__tipo='FAC'
        ).aggregate(total=Sum(F('precio_unitario') * F('cantidad')))['total'] or Decimal('0')
        
        ingresos_por_mes.append(float(ingresos_mes))
        labels_meses.append(fecha_inicio.strftime('%b').upper())
    
    # 2. Servicios por categoría
    from django.db.models import Count
    servicios_por_categoria = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=hace_30_dias
    ).values('servicio__categoria__code').annotate(
        total=Count('id')
    ).order_by('-total')[:4]
    
    categorias_servicios = []
    datos_servicios = []
    for servicio in servicios_por_categoria:
        categorias_servicios.append(servicio['servicio__categoria__code'] or 'Otros')
        datos_servicios.append(servicio['total'])
    
    # Si no hay datos, usar valores por defecto
    if not categorias_servicios:
        categorias_servicios = ['Mecánica', 'Eléctrica', 'Pintura', 'Otros']
        datos_servicios = [0, 0, 0, 0]
    
    # 3. Rendimiento de técnicos
    tecnicos_rendimiento = Tecnico.objects.filter(empresa=empresa).annotate(
        documentos_count=Count('documentos_responsables', filter=Q(documentos_responsables__fecha_emision__gte=hace_30_dias))
    ).order_by('-documentos_count')[:4]
    
    nombres_tecnicos = []
    rendimiento_tecnicos = []
    for tecnico in tecnicos_rendimiento:
        nombres_tecnicos.append(tecnico.nombre)
        rendimiento_tecnicos.append(tecnico.documentos_count)
    
    # Si no hay técnicos, usar valores por defecto
    if not nombres_tecnicos:
        nombres_tecnicos = ['Sin datos']
        rendimiento_tecnicos = [0]
    
    contexto = {
        'empresa': empresa,
        'documentos_total': documentos_total,
        'documentos_mes': documentos_mes,
        'clientes_total': clientes_total,
        'tecnicos_total': tecnicos_total,
        'facturacion_mes': facturacion_mes,
        'ticket_promedio': ticket_promedio,
        'presupuestos': presupuestos,
        'facturas': facturas,
        'ordenes': ordenes,
        'es_dashboard_espacial': True,
        
        # 📊 Datos para gráficos
        'ingresos_por_mes': ingresos_por_mes,
        'labels_meses': labels_meses,
        'categorias_servicios': categorias_servicios,
        'datos_servicios': datos_servicios,
        'nombres_tecnicos': nombres_tecnicos,
        'rendimiento_tecnicos': rendimiento_tecnicos,
    }
    
    # Usar template resolution en lugar de template hardcodeado
    from taller.utils.templates import select_country_lang_template
    from django.utils.translation import get_language, activate
    from django.template.response import TemplateResponse

    # Manejar cambio de idioma
    lang = request.GET.get('lang')
    if lang in ['es', 'en']:
        activate(lang)

    template_name = select_country_lang_template(
        "dashboard/centro_operaciones_espacial.html", 
        getattr(request.user.empresa, 'pais', 'cl').lower(), 
        get_language()
    )

    return render(request, template_name, contexto)


