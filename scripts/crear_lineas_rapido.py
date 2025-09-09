#!/usr/bin/env python
"""
Script rápido para agregar líneas a documento y verificar totales
Ejecutar con: python manage.py shell < crear_lineas_rapido.py
"""

from decimal import Decimal

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio

# Buscar el primer documento
documento = Documento.objects.first()
if documento:
    print(f"📄 Trabajando con documento: {documento.numero} ({documento.tipo})")
    
    # Agregar líneas de repuesto si no existen
    if not documento.lineas_repuesto.exists():
        LineaRepuesto.objects.create(
            documento=documento,
            codigo="REP001",
            nombre="Filtro de Aceite",
            cantidad=2,
            precio_unitario=Decimal('15000.00'),
            descuento=Decimal('0.00')
        )
        
        LineaRepuesto.objects.create(
            documento=documento,
            codigo="REP002", 
            nombre="Pastillas de Freno",
            cantidad=1,
            precio_unitario=Decimal('45000.00'),
            descuento=Decimal('10.00')  # 10% descuento
        )
        print("✅ Líneas de repuesto agregadas")
    
    # Agregar líneas de servicio si no existen
    if not documento.lineas_servicio.exists():
        LineaServicio.objects.create(
            documento=documento,
            codigo="SER001",
            nombre="Cambio de Aceite",
            cantidad=1,
            precio_unitario=Decimal('25000.00'),
            descuento=Decimal('0.00')
        )
        
        LineaServicio.objects.create(
            documento=documento,
            codigo="SER002",
            nombre="Revisión General",
            cantidad=1,
            precio_unitario=Decimal('35000.00'),
            descuento=Decimal('5.00')  # 5% descuento
        )
        print("✅ Líneas de servicio agregadas")
    
    # Verificar totales
    print(f"\n📊 TOTALES:")
    print(f"   Repuestos: ${documento.total_repuestos()}")
    print(f"   Servicios: ${documento.total_servicios()}")
    print(f"   Total: ${documento.total_general()}")
    
    print(f"\n🎉 Datos creados. Recargar la vista para ver los totales!")
else:
    print("❌ No hay documentos en la base de datos")
