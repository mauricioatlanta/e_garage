#!/usr/bin/env python

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
django.setup()

from django.db import connection

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.servicios.models import Servicio


def fix_documento_44_servicios():
    print("🔧 Arreglando servicios del documento 44...")

    try:
        # Obtener el documento 44
        documento = Documento.objects.get(id=44)
        print(f"📄 Documento encontrado: {documento.numero_documento}")

        # Limpiar servicios existentes creados incorrectamente
        cursor = connection.cursor()
        cursor.execute("DELETE FROM taller_lineaservicio WHERE documento_id = 44")
        cursor.execute("DELETE FROM taller_lineaotroservicio WHERE documento_id = 44")
        print("🗑️ Servicios SQL directos eliminados")

        # También limpiar modelos Django
        LineaServicio.objects.filter(documento=documento).delete()
        LineaRepuesto.objects.filter(documento=documento).delete()
        print("🗑️ Modelos Django limpiados")

        # Obtener algunos servicios reales del sistema
        servicios_disponibles = Servicio.objects.all()[:3]
        print(f"⚙️ Servicios disponibles: {servicios_disponibles.count()}")

        if servicios_disponibles.exists():
            # Crear servicios usando modelos Django
            for i, servicio in enumerate(servicios_disponibles, 1):
                linea_servicio = LineaServicio.objects.create(
                    documento=documento,
                    servicio=servicio,
                    nombre=servicio.nombre,
                    cantidad=1,
                    precio_unitario=50000 + (i * 10000),  # Precios variables
                    observaciones=f"Servicio de prueba {i}",
                )
                print(
                    f"✅ Servicio creado: {linea_servicio.nombre} - ${linea_servicio.precio_unitario}"
                )

        # Crear repuestos de ejemplo
        repuestos_ejemplo = [
            ("FIL-001", "Filtro de aceite", 1, 15000),
            ("BUJ-002", "Bujías x4", 4, 8000),
            ("ACE-003", "Aceite motor 5W30", 1, 35000),
        ]

        for codigo, nombre, cantidad, precio in repuestos_ejemplo:
            repuesto = LineaRepuesto.objects.create(
                documento=documento,
                codigo=codigo,
                nombre=nombre,
                cantidad=cantidad,
                precio_unitario=precio,
            )
            print(
                f"✅ Repuesto creado: {repuesto.nombre} x{repuesto.cantidad} - ${repuesto.precio_unitario}"
            )

        # Verificar resultados
        servicios_count = LineaServicio.objects.filter(documento=documento).count()
        repuestos_count = LineaRepuesto.objects.filter(documento=documento).count()

        print("🎯 RESULTADO FINAL:")
        print(f"   📋 Servicios: {servicios_count}")
        print(f"   🔧 Repuestos: {repuestos_count}")

    except Documento.DoesNotExist:
        print("❌ Error: Documento 44 no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    fix_documento_44_servicios()
