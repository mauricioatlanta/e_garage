#!/usr/bin/env python3
"""
Script de prueba para el módulo de inteligencia de negocio
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models.perfilusuario import PerfilUsuario
from taller.models.empresa import Empresa
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.views.business_intelligence import get_servicios_ranking, get_repuestos_utilidad, get_mecanicos_stats
from datetime import datetime, timedelta
from django.utils import timezone

print('🧠 === PRUEBA MÓDULO INTELIGENCIA DE NEGOCIO ===')
print()

# Obtener empresa de prueba
try:
    empresa = Empresa.objects.first()
    if not empresa:
        print('❌ No hay empresas en el sistema')
        exit()
    
    print(f'🏢 Empresa seleccionada: {empresa.nombre_taller}')
    print()
    
    # Fechas de prueba (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    print(f'📅 Período de análisis: {fecha_inicio} a {fecha_fin}')
    print()
    
    # Test 1: Ranking de servicios
    print('📊 === RANKING DE SERVICIOS ===')
    servicios = get_servicios_ranking(empresa, fecha_inicio, fecha_fin)
    if servicios:
        for i, servicio in enumerate(servicios[:5], 1):
            print(f'  {i}. {servicio["nombre"]} - Vendidos: {servicio["cantidad_vendida"]} - Ingresos: ${servicio["ingresos_totales"]:,.0f}')
    else:
        print('  No hay datos de servicios')
    print()
    
    # Test 2: Utilidad de repuestos
    print('💰 === UTILIDAD DE REPUESTOS ===')
    repuestos = get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin)
    if repuestos:
        for i, repuesto in enumerate(repuestos[:5], 1):
            print(f'  {i}. {repuesto["nombre"]} - Utilidad: ${repuesto["utilidad_bruta"]:,.0f} ({repuesto["margen_utilidad"]}%)')
    else:
        print('  No hay datos de repuestos')
    print()
    
    # Test 3: Estadísticas de mecánicos
    print('👨‍🔧 === PERFORMANCE MECÁNICOS ===')
    mecanicos = get_mecanicos_stats(empresa, fecha_inicio, fecha_fin)
    if mecanicos:
        for i, mecanico in enumerate(mecanicos, 1):
            print(f'  {i}. {mecanico["mecanico"].nombre} - Documentos: {mecanico["total_documentos"]} - Ingresos: ${mecanico["ingresos_totales"]:,.0f}')
    else:
        print('  No hay datos de mecánicos')
    print()
    
    # Resumen general
    total_documentos = Documento.objects.filter(empresa=empresa, fecha_emision__range=[fecha_inicio, fecha_fin]).count()
    total_repuestos = RepuestoDocumento.objects.filter(
        documento__empresa=empresa,
        documento__fecha__range=[fecha_inicio, fecha_fin]
    ).count()
    total_servicios = ServicioDocumento.objects.filter(
        empresa=empresa,
        documento__fecha__range=[fecha_inicio, fecha_fin]
    ).count()
    
    print('📈 === RESUMEN GENERAL ===')
    print(f'  Total documentos: {total_documentos}')
    print(f'  Total repuestos vendidos: {total_repuestos}')
    print(f'  Total servicios realizados: {total_servicios}')
    print()
    
    # URLs de acceso
    print('🌐 === ACCESO AL DASHBOARD ===')
    print('  URL principal: http://localhost:8000/taller/business-intelligence/dashboard/')
    print('  APIs disponibles:')
    print('    - Servicios: http://localhost:8000/taller/business-intelligence/api/servicios-ranking/')
    print('    - Repuestos: http://localhost:8000/taller/business-intelligence/api/repuestos-utilidad/')
    print('    - Mecánicos: http://localhost:8000/taller/business-intelligence/api/mecanicos-stats/')
    print()
    
    print('✅ === MÓDULO FUNCIONANDO CORRECTAMENTE ===')
    print('💡 Tip: Accede al dashboard desde el menú principal del sistema')

except Exception as e:
    print(f'❌ Error durante la prueba: {str(e)}')
    import traceback
    traceback.print_exc()
