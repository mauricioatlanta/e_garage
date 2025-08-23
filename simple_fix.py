#!/usr/bin/env python
"""
Script simple para arreglar el documento 44 con datos válidos
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

# Imports
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaServicio, LineaRepuesto
from taller.servicios.models import Servicio
from django.db import connection

# Función principal
def fix_it():
    print("🛠️ Iniciando reparación del documento 44...")
    
    # Obtener documento
    documento = Documento.objects.get(id=44)
    print(f"✅ Documento: {documento.numero_documento}")
    
    # Limpiar
    cursor = connection.cursor()
    cursor.execute("DELETE FROM taller_lineaservicio WHERE documento_id = 44")
    cursor.execute("DELETE FROM taller_lineaotroservicio WHERE documento_id = 44")
    LineaServicio.objects.filter(documento=documento).delete()
    LineaRepuesto.objects.filter(documento=documento).delete()
    print("🗑️ Datos anteriores eliminados")
    
    # Verificar servicios disponibles
    servicios = list(Servicio.objects.all()[:3])
    print(f"📋 Servicios disponibles: {len(servicios)}")
    
    # Crear servicios
    if servicios:
        for i, servicio in enumerate(servicios):
            ls = LineaServicio.objects.create(
                documento=documento,
                servicio=servicio,
                nombre=servicio.nombre,
                cantidad=1,
                precio_unitario=45000 + (i * 5000)
            )
            print(f"✅ Servicio: {ls.nombre} - ${ls.precio_unitario}")
    else:
        print("⚠️ No hay servicios en el sistema, creando servicio básico...")
        # Si no hay servicios, crear uno básico
        servicio_basico = Servicio.objects.create(
            nombre="Servicio Básico",
            descripcion="Servicio de prueba",
            precio_base=40000
        )
        ls = LineaServicio.objects.create(
            documento=documento,
            servicio=servicio_basico,
            nombre=servicio_basico.nombre,
            cantidad=1,
            precio_unitario=40000
        )
        print(f"✅ Servicio creado: {ls.nombre}")
    
    # Crear repuestos
    repuestos_datos = [
        ("FILT-001", "Filtro de aceite", 1, 18000),
        ("BUJ-002", "Bujías NGK", 4, 6500),
        ("ACEI-003", "Aceite 5W30", 1, 32000)
    ]
    
    for codigo, nombre, cantidad, precio in repuestos_datos:
        rep = LineaRepuesto.objects.create(
            documento=documento,
            codigo=codigo,
            nombre=nombre,
            cantidad=cantidad,
            precio_unitario=precio
        )
        print(f"✅ Repuesto: {rep.nombre} x{rep.cantidad} - ${rep.precio_unitario}")
    
    # Verificar resultado
    servicios_final = LineaServicio.objects.filter(documento=documento).count()
    repuestos_final = LineaRepuesto.objects.filter(documento=documento).count()
    
    print(f"\n🎯 RESULTADO:")
    print(f"📋 Servicios: {servicios_final}")
    print(f"🔧 Repuestos: {repuestos_final}")
    print("✅ Documento 44 listo para edición!")

if __name__ == '__main__':
    try:
        fix_it()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
