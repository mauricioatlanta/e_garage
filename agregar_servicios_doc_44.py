#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from decimal import Decimal

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaOtroServicio, LineaServicio
from taller.models.servicios import ServicioInterno


def agregar_servicios_doc_44():
    """Agregar servicios al documento 44 si no los tiene"""
    try:
        doc = Documento.objects.get(id=44)
        print(f"=== AGREGANDO SERVICIOS AL DOCUMENTO {doc.id} ===")
        print(f"Documento: {doc.numero_documento}")

        # Verificar servicios existentes
        servicios_existentes = LineaServicio.objects.filter(documento=doc).count()
        otros_existentes = LineaOtroServicio.objects.filter(documento=doc).count()

        print(f"Servicios existentes: {servicios_existentes}")
        print(f"Otros servicios existentes: {otros_existentes}")

        # Si no tiene servicios, agregar algunos
        if servicios_existentes == 0:
            print("\n📝 Agregando servicios internos...")

            # Crear línea de servicio 1
            LineaServicio.objects.create(
                documento=doc,
                servicio=None,  # Servicio personalizado
                codigo="SER-001",
                nombre="Cambio de aceite",
                cantidad=1,
                precio_unitario=Decimal("25.00"),
                descuento=Decimal("0.00"),
            )

            # Crear línea de servicio 2
            LineaServicio.objects.create(
                documento=doc,
                servicio=None,  # Servicio personalizado
                codigo="SER-002",
                nombre="Revisión de frenos",
                cantidad=1,
                precio_unitario=Decimal("35.00"),
                descuento=Decimal("0.00"),
            )

            print("✅ Servicios internos agregados")

        # Si no tiene otros servicios, agregar algunos
        if otros_existentes == 0:
            print("\n📝 Agregando otros servicios...")

            # Crear línea de otro servicio
            LineaOtroServicio.objects.create(
                documento=doc,
                servicio_externo=None,
                nombre="Instalación de Audio",
                empresa_externa="AudioCar Professional",
                cantidad=1,
                costo_interno=Decimal("20.00"),
                precio_cliente=Decimal("35.00"),
                ganancia=Decimal("15.00"),
            )

            print("✅ Otros servicios agregados")

        # Actualizar kilometraje del vehículo si no lo tiene
        if not getattr(doc.vehiculo, "millas", None):
            doc.vehiculo.millas = 85000
            doc.vehiculo.save()
            print("✅ Kilometraje del vehículo actualizado a 85,000")

        # Recalcular totales del documento
        servicios_total = LineaServicio.objects.filter(documento=doc).aggregate(
            total=models.Sum(models.F("cantidad") * models.F("precio_unitario"))
        )["total"] or Decimal("0.00")

        otros_total = LineaOtroServicio.objects.filter(documento=doc).aggregate(
            total=models.Sum(models.F("cantidad") * models.F("precio_cliente"))
        )["total"] or Decimal("0.00")

        # Actualizar totales en el documento
        doc.neto_servicios = servicios_total + otros_total
        doc.save()

        print(f"\n💰 Totales actualizados:")
        print(f"Servicios: ${servicios_total}")
        print(f"Otros servicios: ${otros_total}")
        print(f"Total servicios: ${doc.neto_servicios}")

        print(f"\n✅ Documento {doc.id} actualizado exitosamente")
        return True

    except Documento.DoesNotExist:
        print("❌ Documento 44 no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    from django.db import models

    success = agregar_servicios_doc_44()
    if success:
        print("\n🎉 ¡Servicios agregados correctamente!")
        print("Ahora puedes verificar http://127.0.0.1:8000/us/documentos/44/")
    else:
        print("\n💥 No se pudieron agregar los servicios")
