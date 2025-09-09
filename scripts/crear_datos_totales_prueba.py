#!/usr/bin/env python
import os
import sys
from decimal import Decimal

import django

# Configurar Django
sys.path.insert(0, r'e:\projecto\e_garage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'egarage.settings')
django.setup()

from datetime import date

from taller.models.base_models import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio

try:
    print("🔍 Iniciando creación de datos de prueba para totales...")
    
    # Buscar o crear un cliente
    cliente, created = Cliente.objects.get_or_create(
        rut="12345678-9",
        defaults={
            'nombre': "Cliente Prueba",
            'email': "prueba@test.com"
        }
    )
    if created:
        print(f"✅ Cliente creado: {cliente.nombre}")
    else:
        print(f"📋 Cliente encontrado: {cliente.nombre}")
    
    # Crear documento de prueba
    documento = Documento.objects.create(
        numero=9999,
        tipo="COTIZACION",
        cliente=cliente,
        fecha=date.today(),
        descuento=Decimal('0.00'),
        tax_rate_applied=Decimal('19.00')
    )
    print(f"✅ Documento creado: {documento.numero}")
    
    # Agregar líneas de repuestos
    linea_repuesto1 = LineaRepuesto.objects.create(
        documento=documento,
        codigo="REP001",
        nombre="Filtro de Aceite",
        cantidad=2,
        precio_unitario=Decimal('15000.00'),
        descuento=Decimal('0.00')
    )
    
    linea_repuesto2 = LineaRepuesto.objects.create(
        documento=documento,
        codigo="REP002", 
        nombre="Pastillas de Freno",
        cantidad=1,
        precio_unitario=Decimal('45000.00'),
        descuento=Decimal('10.00')  # 10% descuento
    )
    
    print(f"✅ Líneas de repuesto creadas:")
    print(f"   - {linea_repuesto1.nombre}: {linea_repuesto1.cantidad} x ${linea_repuesto1.precio_unitario} = ${linea_repuesto1.subtotal}")
    print(f"   - {linea_repuesto2.nombre}: {linea_repuesto2.cantidad} x ${linea_repuesto2.precio_unitario} (desc. {linea_repuesto2.descuento}%) = ${linea_repuesto2.subtotal}")
    
    # Agregar líneas de servicios
    linea_servicio1 = LineaServicio.objects.create(
        documento=documento,
        codigo="SER001",
        nombre="Cambio de Aceite",
        cantidad=1,
        precio_unitario=Decimal('25000.00'),
        descuento=Decimal('0.00')
    )
    
    linea_servicio2 = LineaServicio.objects.create(
        documento=documento,
        codigo="SER002",
        nombre="Revisión General",
        cantidad=1,
        precio_unitario=Decimal('35000.00'),
        descuento=Decimal('5.00')  # 5% descuento
    )
    
    print(f"✅ Líneas de servicio creadas:")
    print(f"   - {linea_servicio1.nombre}: {linea_servicio1.cantidad} x ${linea_servicio1.precio_unitario} = ${linea_servicio1.subtotal}")
    print(f"   - {linea_servicio2.nombre}: {linea_servicio2.cantidad} x ${linea_servicio2.precio_unitario} (desc. {linea_servicio2.descuento}%) = ${linea_servicio2.subtotal}")
    
    # Verificar totales
    print(f"\n📊 TOTALES DEL DOCUMENTO {documento.numero}:")
    print(f"   Total Repuestos: ${documento.total_repuestos()}")
    print(f"   Total Servicios: ${documento.total_servicios()}")
    print(f"   IVA: ${documento.iva()}")
    print(f"   Total General: ${documento.total_general()}")
    
    print(f"\n🎯 Datos de prueba creados exitosamente!")
    print(f"   El documento {documento.numero} ahora debería mostrar totales en la vista")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
