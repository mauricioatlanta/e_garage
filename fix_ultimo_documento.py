#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from decimal import Decimal

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaOtroServicio, LineaServicio


def agregar_servicios_ultimo_documento():
    """Agregar servicios al último documento existente"""
    try:
        # Buscar el último documento
        doc = Documento.objects.last()
        if not doc:
            print("❌ No hay documentos en la base de datos")
            return False

        print(f"=== AGREGANDO SERVICIOS AL ÚLTIMO DOCUMENTO ===")
        print(f"ID: {doc.pk}")
        print(f"Número: {doc.numero_documento}")
        print(f"Cliente: {doc.cliente.nombre} {doc.cliente.apellido}")

        # Verificar servicios existentes
        servicios_count = LineaServicio.objects.filter(documento=doc).count()
        otros_count = LineaOtroServicio.objects.filter(documento=doc).count()

        print(f"Servicios existentes: {servicios_count}")
        print(f"Otros servicios existentes: {otros_count}")

        # Agregar servicios si no existen
        if servicios_count == 0:
            print("\n📝 Agregando servicios internos...")

            LineaServicio.objects.create(
                documento=doc,
                servicio=None,
                codigo="SER-001",
                nombre="Cambio de aceite motor",
                cantidad=1,
                precio_unitario=Decimal("30.00"),
                descuento=Decimal("0.00"),
            )

            LineaServicio.objects.create(
                documento=doc,
                servicio=None,
                codigo="SER-002",
                nombre="Revisión de frenos completa",
                cantidad=1,
                precio_unitario=Decimal("45.00"),
                descuento=Decimal("0.00"),
            )

            print("✅ 2 servicios internos agregados")

        # Agregar otros servicios si no existen
        if otros_count == 0:
            print("\n📝 Agregando otros servicios...")

            LineaOtroServicio.objects.create(
                documento=doc,
                servicio_externo=None,
                nombre="Instalación de Audio y Video",
                empresa_externa="AudioCar Professional",
                cantidad=1,
                costo_interno=Decimal("25.00"),
                precio_cliente=Decimal("40.00"),
                ganancia=Decimal("15.00"),
            )

            LineaOtroServicio.objects.create(
                documento=doc,
                servicio_externo=None,
                nombre="Polarizado de ventanas",
                empresa_externa="TintPro Services",
                cantidad=1,
                costo_interno=Decimal("35.00"),
                precio_cliente=Decimal("60.00"),
                ganancia=Decimal("25.00"),
            )

            print("✅ 2 otros servicios agregados")

        # Actualizar kilometraje del vehículo
        if hasattr(doc.vehiculo, "millas"):
            if not doc.vehiculo.millas:
                doc.vehiculo.millas = 95000
                doc.vehiculo.save()
                print("✅ Kilometraje actualizado a 95,000 millas")

        # Recalcular totales
        from django.db.models import F, Sum

        servicios_total = LineaServicio.objects.filter(documento=doc).aggregate(
            total=Sum(F("cantidad") * F("precio_unitario"))
        )["total"] or Decimal("0.00")

        otros_total = LineaOtroServicio.objects.filter(documento=doc).aggregate(
            total=Sum(F("cantidad") * F("precio_cliente"))
        )["total"] or Decimal("0.00")

        # Actualizar totales del documento
        doc.neto_servicios = servicios_total + otros_total
        doc.save()

        print(f"\n💰 TOTALES RECALCULADOS:")
        print(f"Servicios internos: ${servicios_total}")
        print(f"Otros servicios: ${otros_total}")
        print(f"Total servicios: ${doc.neto_servicios}")
        print(f"Total documento: ${doc.total}")

        print(f"\n🎉 ¡DOCUMENTO {doc.pk} ACTUALIZADO!")
        print(f"Ver en: http://127.0.0.1:8000/us/documentos/{doc.pk}/")

        return doc.pk

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    doc_id = agregar_servicios_ultimo_documento()
    if doc_id:
        print(f"\n✅ Listo! Accede a http://127.0.0.1:8000/us/documentos/{doc_id}/")
    else:
        print("\n❌ No se pudo completar la operación")
