#!/usr/bin/env python
"""
Script directo para crear líneas de documentos y probar totales
"""

import os
import sys

sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

import django

django.setup()

from decimal import Decimal

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio


def main():
    print("🔍 Diagnosticando problema de totales...")

    # 1. Verificar documentos
    docs = Documento.objects.all()
    print(f"📄 Total documentos: {docs.count()}")

    if not docs.exists():
        print("❌ No hay documentos. Ejecuta primero crear_datos_prueba_i18n_simple.py")
        return

    # 2. Tomar primer documento
    doc = docs.first()
    print(f"📋 Documento seleccionado: ID={doc.pk}")

    # 3. Verificar líneas existentes
    rep_count = doc.lineas_repuesto.count()
    serv_count = doc.lineas_servicio.count()
    otros_count = doc.lineas_otro_servicio.count()

    print(f"🔧 Líneas de repuestos: {rep_count}")
    print(f"🛠️ Líneas de servicios: {serv_count}")
    print(f"🏢 Líneas otros servicios: {otros_count}")

    # 4. Si no hay líneas, crear algunas
    if rep_count == 0 and serv_count == 0:
        print("➕ Creando líneas de ejemplo...")

        # Crear línea de servicio
        linea_serv = LineaServicio.objects.create(
            documento=doc,
            nombre="Cambio de aceite",
            cantidad=1,
            precio_unitario=Decimal("50000"),
            descuento=Decimal("0"),
        )
        print(f"✅ Servicio creado: {linea_serv.nombre} - Subtotal: {linea_serv.subtotal}")

        # Crear línea de repuesto
        linea_rep = LineaRepuesto.objects.create(
            documento=doc,
            codigo="REP-001",
            nombre="Filtro de aceite",
            cantidad=1,
            precio_unitario=Decimal("15000"),
            descuento=Decimal("0"),
        )
        print(f"✅ Repuesto creado: {linea_rep.nombre} - Subtotal: {linea_rep.subtotal}")

    # 5. Probar métodos de totales
    print("\n💰 Probando cálculos de totales:")

    try:
        total_rep = doc.total_repuestos()
        print(f"   Repuestos: {total_rep}")
    except Exception as e:
        print(f"   ❌ Error repuestos: {e}")

    try:
        total_serv = doc.total_servicios()
        print(f"   Servicios: {total_serv}")
    except Exception as e:
        print(f"   ❌ Error servicios: {e}")

    try:
        total_gen = doc.total_general()
        print(f"   Total General: {total_gen}")
    except Exception as e:
        print(f"   ❌ Error total general: {e}")

    # 6. Verificar líneas individuales
    print("\n🔍 Detalles de líneas:")
    for linea in doc.lineas_repuesto.all():
        print(
            f"   🔧 {linea.nombre}: {linea.cantidad} x {linea.precio_unitario} = {linea.subtotal}"
        )

    for linea in doc.lineas_servicio.all():
        print(f"   🛠️ {linea.nombre}: {linea.cantidad} x {linea.precio_unitario} = {linea.subtotal}")

    print("\n✅ Diagnóstico completado!")


if __name__ == "__main__":
    main()
