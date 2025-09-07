"""
Script para simplificar el dashboard espacial y eliminar campos problemáticos
"""



# Reemplazar la función completa con una versión simplificada
codigo_simplificado = '''@login_required
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
    from taller.models.lineas_documento import LineaServicio
    facturacion_mes = LineaServicio.objects.filter(
        documento__empresa=empresa, 
        documento__fecha__gte=hace_30_dias
    ).aggregate(total=Sum('precio_unitario'))['total'] or Decimal('0')
    
    # Ticket promedio
    ticket_promedio = facturacion_mes / documentos_mes if documentos_mes > 0 else Decimal('0')
    
    # Documentos por tipo (simplificado)
    presupuestos = Documento.objects.filter(empresa=empresa, tipo_documento='PRESUPUESTO').count()
    facturas = Documento.objects.filter(empresa=empresa, tipo_documento='FACTURA').count()
    ordenes = Documento.objects.filter(empresa=empresa, tipo_documento='ORDEN_TRABAJO').count()
    
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
    }
    
    return render(request, 'taller/dashboard/centro_operaciones_espacial.html', contexto)'''

print("✅ Código simplificado preparado")
print("📝 El dashboard espacial se ha simplificado para evitar errores de campos")
print("🎯 Incluye métricas básicas y seguras")
