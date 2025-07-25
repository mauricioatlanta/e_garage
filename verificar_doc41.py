#!/usr/bin/env python3
"""
Verificar si el documento 41 se creó correctamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento

print('🔍 === VERIFICAR DOCUMENTO 41 ===')

try:
    doc = Documento.objects.get(pk=41)
    print(f'✅ Documento encontrado: {doc.pk}')
    print(f'   - Empresa: {doc.empresa.nombre_taller}')
    print(f'   - Número: {doc.numero_documento}')
    print(f'   - Tipo: {doc.tipo_documento}')
    print(f'   - Cliente: {doc.cliente}')
    print(f'   - Fecha: {doc.fecha}')
    print(f'   - Observaciones: {doc.observaciones}')
    
    # Verificar repuestos
    repuestos = RepuestoDocumento.objects.filter(documento=doc)
    print(f'\n📦 Repuestos ({repuestos.count()}):')
    for rep in repuestos:
        print(f'   - {rep.codigo}: {rep.nombre} x{rep.cantidad} = ${rep.precio:,}')
    
    # Verificar servicios
    servicios = ServicioDocumento.objects.filter(documento=doc)
    print(f'\n🔧 Servicios ({servicios.count()}):')
    for serv in servicios:
        print(f'   - {serv.nombre} = ${serv.precio:,}')
    
    # Calcular total
    total_repuestos = sum(r.total for r in repuestos)
    total_servicios = sum(s.precio for s in servicios)
    total_documento = total_repuestos + total_servicios
    
    print(f'\n💰 Totales:')
    print(f'   - Repuestos: ${total_repuestos:,}')
    print(f'   - Servicios: ${total_servicios:,}')
    print(f'   - TOTAL: ${total_documento:,}')
    
    if repuestos.count() == 0 and servicios.count() == 0:
        print('\n❌ PROBLEMA: El documento no tiene repuestos ni servicios')
    elif repuestos.count() > 0 and servicios.count() > 0:
        print('\n✅ ÉXITO: El documento tiene repuestos y servicios')
    else:
        print('\n⚠️ PARCIAL: El documento tiene solo repuestos O servicios')

except Documento.DoesNotExist:
    print('❌ Documento 41 no encontrado')

print('\n🏁 === FIN VERIFICACIÓN ===')
