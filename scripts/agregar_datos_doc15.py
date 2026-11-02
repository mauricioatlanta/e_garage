import os
import sys

import django

sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.tecnico import Tecnico


def agregar_datos_documento_15():
    """Agregar datos al documento #15 para testing de edición"""

    print("🔧 AGREGANDO DATOS AL DOCUMENTO #15")

    try:
        documento = Documento.objects.get(id=15)
        print(f"📋 Documento encontrado: {documento.tipo_documento} #{documento.numero_documento}")

        # Agregar técnico
        tecnico, _ = Tecnico.objects.get_or_create(nombre="Juan Pérez")
        documento.tecnico = tecnico
        documento.save()
        print(f"🔧 Técnico asignado: {tecnico.nombre}")

        # Agregar repuestos
        repuestos_data = [
            {
                "codigo": "FIL001",
                "nombre": "Filtro de aceite Toyota",
                "cantidad": 2,
                "precio": 15000,
            },
            {
                "codigo": "ACE001",
                "nombre": "Aceite 5W30 4L",
                "cantidad": 1,
                "precio": 35000,
            },
        ]

        for rep_data in repuestos_data:
            repuesto = LineaRepuesto.objects.create(
                documento=documento,
                codigo=rep_data["codigo"],
                nombre=rep_data["nombre"],
                cantidad=rep_data["cantidad"],
                precio_unitario=rep_data["precio"],
            )
            print(f"🔩 Repuesto agregado: {repuesto.nombre}")

        # Agregar servicios
        servicios_data = [
            {"nombre": "Cambio de aceite completo", "precio": 25000},
            {"nombre": "Revisión de frenos", "precio": 15000},
        ]

        empresa = documento.empresa
        for serv_data in servicios_data:
            servicio = LineaServicio.objects.create(
                documento=documento,
                nombre=serv_data["nombre"],
                precio_unitario=serv_data["precio"],
            )
            print(f"⚙️ Servicio agregado: {servicio.nombre}")

        # Verificar totales (accesos defensivos a nombres de campo)
        repuestos = LineaRepuesto.objects.filter(documento=documento)
        servicios = LineaServicio.objects.filter(documento=documento)

        total_repuestos = sum(
            (getattr(r, "precio_unitario", getattr(r, "precio", 0)) * getattr(r, "cantidad", 1))
            for r in repuestos
        )
        total_servicios = sum(
            getattr(s, "precio_unitario", getattr(s, "precio", 0)) for s in servicios
        )
        total_general = total_repuestos + total_servicios

        print("\n💰 TOTALES CALCULADOS:")
        print(f"   Repuestos: ${total_repuestos}")
        print(f"   Servicios: ${total_servicios}")
        print(f"   TOTAL: ${total_general}")

        print("\n🔗 URL para probar edición: http://127.0.0.1:8000/documentos/editar/15/")

        return True

    except Documento.DoesNotExist:
        print("❌ Documento #15 no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    agregar_datos_documento_15()
