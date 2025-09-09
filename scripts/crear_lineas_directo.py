#!/usr/bin/env python
"""
Script directo para crear líneas de documento - ejecutar en el directorio del proyecto
"""

import os
import sys
from decimal import Decimal

import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "egarage.settings")

try:
    django.setup()
    print("✅ Django configurado")

    from taller.models.documento import Documento
    from taller.models.lineas_documento import LineaRepuesto, LineaServicio

    # Verificar documentos
    documentos = Documento.objects.all()
    print(f"📄 Total documentos: {documentos.count()}")

    if not documentos.exists():
        print("❌ No hay documentos en la base de datos")
        sys.exit(1)

    # Verificar líneas existentes
    total_lineas_rep = LineaRepuesto.objects.count()
    total_lineas_serv = LineaServicio.objects.count()
    print(
        f"📊 Líneas existentes - Repuestos: {total_lineas_rep}, Servicios: {total_lineas_serv}"
    )

    # Tomar primer documento
    documento = documentos.first()
    print(f"🎯 Trabajando con documento: {documento.numero} ({documento.tipo})")

    # Verificar estado actual
    lineas_rep = documento.lineas_repuesto.count()
    lineas_serv = documento.lineas_servicio.count()
    print(f"📋 Estado actual - Repuestos: {lineas_rep}, Servicios: {lineas_serv}")

    # Crear líneas de repuesto
    if lineas_rep == 0:
        print("🔧 Creando líneas de repuesto...")

        linea1 = LineaRepuesto.objects.create(
            documento=documento,
            codigo="REP001",
            nombre="Filtro de Aceite",
            cantidad=2,
            precio_unitario=Decimal("15000.00"),
            descuento=Decimal("0.00"),
        )

        linea2 = LineaRepuesto.objects.create(
            documento=documento,
            codigo="REP002",
            nombre="Pastillas de Freno",
            cantidad=1,
            precio_unitario=Decimal("45000.00"),
            descuento=Decimal("10.00"),
        )

        print("✅ Repuestos creados:")
        print(
            f"   - {linea1.nombre}: {linea1.cantidad} x ${linea1.precio_unitario} = ${linea1.subtotal}"
        )
        print(
            f"   - {linea2.nombre}: {linea2.cantidad} x ${linea2.precio_unitario} (desc: {linea2.descuento}%) = ${linea2.subtotal}"
        )

    # Crear líneas de servicio
    if lineas_serv == 0:
        print("⚙️ Creando líneas de servicio...")

        linea3 = LineaServicio.objects.create(
            documento=documento,
            codigo="SER001",
            nombre="Cambio de Aceite",
            cantidad=1,
            precio_unitario=Decimal("25000.00"),
            descuento=Decimal("0.00"),
        )

        linea4 = LineaServicio.objects.create(
            documento=documento,
            codigo="SER002",
            nombre="Revisión General",
            cantidad=1,
            precio_unitario=Decimal("35000.00"),
            descuento=Decimal("5.00"),
        )

        print("✅ Servicios creados:")
        print(
            f"   - {linea3.nombre}: {linea3.cantidad} x ${linea3.precio_unitario} = ${linea3.subtotal}"
        )
        print(
            f"   - {linea4.nombre}: {linea4.cantidad} x ${linea4.precio_unitario} (desc: {linea4.descuento}%) = ${linea4.subtotal}"
        )

    # Verificar totales
    print("\n📊 TOTALES FINALES:")
    total_rep = documento.total_repuestos()
    total_serv = documento.total_servicios()
    total_gen = documento.total_general()

    print(f"   Total Repuestos: ${total_rep}")
    print(f"   Total Servicios: ${total_serv}")
    print(f"   Total General: ${total_gen}")

    if total_rep > 0 or total_serv > 0:
        print("\n🎉 ¡ÉXITO! Recargar:")
        print("   - US: http://127.0.0.1:8000/us/documentos/us/")
        print("   - CL: http://127.0.0.1:8000/cl/documentos/cl/")
    else:
        print("\n⚠️ Los totales siguen en 0")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
