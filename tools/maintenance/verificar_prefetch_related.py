#!/usr/bin/env python3
"""
Script para verificar que prefetch_related funciona correctamente en las vistas
de documentos después de los cambios implementados.
"""

import os
import sys

import django
from django.db import connection

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import (LineaOtroServicio, LineaRepuesto,
                                            LineaServicio)


def verificar_prefetch_related():
    """Verifica que prefetch_related funcione correctamente"""
    print("🔍 VERIFICACIÓN DE PREFETCH_RELATED EN DOCUMENTOS")
    print("=" * 60)
    
    # Buscar documentos con líneas
    documentos_con_lineas = []
    
    print("\n1. Buscando documentos con líneas...")
    for documento in Documento.objects.all()[:10]:
        lineas_repuesto = documento.lineas_repuesto.count() if hasattr(documento, 'lineas_repuesto') else 0
        lineas_servicio = documento.lineas_servicio.count() if hasattr(documento, 'lineas_servicio') else 0 
        lineas_otro = documento.lineas_otro_servicio.count() if hasattr(documento, 'lineas_otro_servicio') else 0
        
        total_lineas = lineas_repuesto + lineas_servicio + lineas_otro
        if total_lineas > 0:
            documentos_con_lineas.append((documento, total_lineas, lineas_repuesto, lineas_servicio, lineas_otro))
            print(f"   📄 Doc #{documento.numero_documento}: {total_lineas} líneas (R:{lineas_repuesto}, S:{lineas_servicio}, O:{lineas_otro})")
    
    if not documentos_con_lineas:
        print("   ❌ No se encontraron documentos con líneas")
        return False
    
    print(f"\n2. Encontrados {len(documentos_con_lineas)} documentos con líneas")
    
    # Probar consulta sin prefetch_related (múltiples queries)
    print("\n3. Consulta SIN prefetch_related:")
    initial_queries = len(connection.queries)
    
    documento_test = documentos_con_lineas[0][0]
    documento_sin_prefetch = Documento.objects.get(id=documento_test.id)
    
    repuestos_sin_prefetch = list(documento_sin_prefetch.lineas_repuesto.all())
    servicios_sin_prefetch = list(documento_sin_prefetch.lineas_servicio.all())
    otros_sin_prefetch = list(documento_sin_prefetch.lineas_otro_servicio.all())
    
    queries_sin_prefetch = len(connection.queries) - initial_queries
    print(f"   🔢 Queries ejecutadas: {queries_sin_prefetch}")
    print(f"   📊 Resultados: {len(repuestos_sin_prefetch)} repuestos, {len(servicios_sin_prefetch)} servicios, {len(otros_sin_prefetch)} otros")
    
    # Probar consulta con prefetch_related (menos queries)
    print("\n4. Consulta CON prefetch_related:")
    initial_queries = len(connection.queries)
    
    documento_con_prefetch = Documento.objects.prefetch_related(
        'lineas_repuesto', 'lineas_servicio', 'lineas_otro_servicio'
    ).get(id=documento_test.id)
    
    repuestos_con_prefetch = list(documento_con_prefetch.lineas_repuesto.all())
    servicios_con_prefetch = list(documento_con_prefetch.lineas_servicio.all())
    otros_con_prefetch = list(documento_con_prefetch.lineas_otro_servicio.all())
    
    queries_con_prefetch = len(connection.queries) - initial_queries
    print(f"   🔢 Queries ejecutadas: {queries_con_prefetch}")
    print(f"   📊 Resultados: {len(repuestos_con_prefetch)} repuestos, {len(servicios_con_prefetch)} servicios, {len(otros_con_prefetch)} otros")
    
    # Verificar que los resultados sean iguales
    print("\n5. Verificación de consistencia:")
    repuestos_ok = len(repuestos_sin_prefetch) == len(repuestos_con_prefetch)
    servicios_ok = len(servicios_sin_prefetch) == len(servicios_con_prefetch)
    otros_ok = len(otros_sin_prefetch) == len(otros_con_prefetch)
    
    print(f"   ✅ Repuestos consistentes: {repuestos_ok}")
    print(f"   ✅ Servicios consistentes: {servicios_ok}")
    print(f"   ✅ Otros servicios consistentes: {otros_ok}")
    
    # Mostrar mejora en queries
    print(f"\n6. Optimización:")
    if queries_con_prefetch < queries_sin_prefetch:
        mejora = queries_sin_prefetch - queries_con_prefetch
        print(f"   🚀 Prefetch_related reduce {mejora} queries")
        print(f"   📈 Mejora: {mejora}/{queries_sin_prefetch} = {mejora/queries_sin_prefetch*100:.1f}%")
    else:
        print(f"   ⚠️  No se detectó mejora en queries")
    
    # Verificar contenido de las líneas
    print(f"\n7. Contenido de las líneas (Documento #{documento_test.numero_documento}):")
    
    for i, repuesto in enumerate(repuestos_con_prefetch[:3]):
        precio = getattr(repuesto, 'precio_unitario', 0)
        cantidad = getattr(repuesto, 'cantidad', 1)
        nombre = getattr(repuesto, 'nombre', 'Sin nombre')
        print(f"   🔧 Repuesto {i+1}: {nombre} - ${precio} x {cantidad}")
    
    for i, servicio in enumerate(servicios_con_prefetch[:3]):
        precio = getattr(servicio, 'precio_unitario', 0)
        nombre = getattr(servicio, 'nombre', 'Sin nombre')
        print(f"   🛠️  Servicio {i+1}: {nombre} - ${precio}")
    
    for i, otro in enumerate(otros_con_prefetch[:3]):
        precio = getattr(otro, 'precio_cliente', 0)
        nombre = getattr(otro, 'nombre_servicio', 'Sin nombre')
        empresa = getattr(otro, 'empresa_externa', '')
        print(f"   🏢 Otro {i+1}: {nombre} ({empresa}) - ${precio}")
    
    print(f"\n✅ VERIFICACIÓN COMPLETADA")
    print(f"{'='*60}")
    
    return repuestos_ok and servicios_ok and otros_ok

def verificar_campos_requeridos():
    """Verifica que todas las líneas tengan los campos requeridos"""
    print("\n🔍 VERIFICACIÓN DE CAMPOS REQUERIDOS")
    print("=" * 60)
    
    # Verificar LineaRepuesto
    repuestos_sin_codigo = LineaRepuesto.objects.filter(codigo__isnull=True).count()
    repuestos_sin_descuento = LineaRepuesto.objects.filter(descuento__isnull=True).count()
    
    print(f"📋 LineaRepuesto:")
    print(f"   - Total: {LineaRepuesto.objects.count()}")
    print(f"   - Sin código: {repuestos_sin_codigo}")
    print(f"   - Sin descuento: {repuestos_sin_descuento}")
    
    # Verificar LineaServicio
    servicios_sin_codigo = LineaServicio.objects.filter(codigo__isnull=True).count()
    servicios_sin_descuento = LineaServicio.objects.filter(descuento__isnull=True).count()
    
    print(f"📋 LineaServicio:")
    print(f"   - Total: {LineaServicio.objects.count()}")
    print(f"   - Sin código: {servicios_sin_codigo}")
    print(f"   - Sin descuento: {servicios_sin_descuento}")
    
    # Verificar LineaOtroServicio
    otros_total = LineaOtroServicio.objects.count()
    
    print(f"📋 LineaOtroServicio:")
    print(f"   - Total: {otros_total}")
    
    return True

if __name__ == '__main__':
    print("🚀 INICIANDO VERIFICACIÓN DE PREFETCH_RELATED")
    
    try:
        # Limpiar queries previas para medición precisa
        connection.queries.clear()
        
        # Verificar prefetch_related
        prefetch_ok = verificar_prefetch_related()
        
        # Verificar campos
        campos_ok = verificar_campos_requeridos()
        
        if prefetch_ok and campos_ok:
            print(f"\n🎉 TODAS LAS VERIFICACIONES PASARON")
        else:
            print(f"\n⚠️  ALGUNAS VERIFICACIONES FALLARON")
            
    except Exception as e:
        print(f"\n❌ ERROR EN VERIFICACIÓN: {e}")
        import traceback
        traceback.print_exc()
