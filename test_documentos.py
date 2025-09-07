import os
import sys

import django

sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from taller.models import Documento


def test_documento_completo(doc_id):
    try:
        doc = Documento.objects.get(id=doc_id)
        print(f"\n📄 DOCUMENTO #{doc_id} - {doc.tipo_documento} {doc.numero_documento}")
        print(f"📅 Fecha: {doc.fecha}")
        print(f"👤 Cliente: {doc.cliente}")
        print(f"🚗 Vehículo: {doc.vehiculo}")
        print(f"📊 Kilometraje: {doc.kilometraje}")
        print(f"📝 Observaciones: {doc.observaciones}")
        print(f"👨‍🔧 Mecánico: {doc.mecanico}")
        print(f"🏢 Empresa: {doc.empresa}")

        repuestos = doc.repuestos.all()
        servicios = doc.servicios.all()

        print(f"\n🔧 REPUESTOS ({repuestos.count()}):")
        total_repuestos = 0
        for rep in repuestos:
            print(f"   📦 {rep.codigo} - {rep.nombre}")
            print(
                f"      Cantidad: {rep.cantidad} | Precio: ${rep.precio:,} | Total: ${rep.total:,}"
            )
            total_repuestos += rep.total

        print(f"\n⚙️ SERVICIOS ({servicios.count()}):")
        total_servicios = 0
        for serv in servicios:
            print(f"   🔧 {serv.nombre} - ${serv.precio:,}")
            total_servicios += serv.precio

        subtotal = total_repuestos + total_servicios
        iva = subtotal * 0.19
        total = subtotal + iva

        print(f"\n💰 TOTALES:")
        print(f"   Repuestos: ${total_repuestos:,}")
        print(f"   Servicios: ${total_servicios:,}")
        print(f"   Subtotal: ${subtotal:,}")
        print(f"   IVA: ${iva:,.0f}")
        print(f"   TOTAL: ${total:,.0f}")

        print(f"\n✅ VALIDACIÓN:")
        print(f"   ✅ Tiene fecha: {doc.fecha is not None}")
        print(f"   ✅ Tiene cliente: {doc.cliente is not None}")
        print(f"   ✅ Tiene repuestos: {repuestos.count() > 0}")
        print(f"   ✅ Tiene servicios: {servicios.count() > 0}")
        print(f"   ✅ Cálculos correctos: {total > 0}")

        return True

    except Documento.DoesNotExist:
        print(f"❌ Documento {doc_id} no existe")
        return False
    except Exception as e:
        print(f"❌ Error al validar documento {doc_id}: {e}")
        return False


# Probar múltiples documentos
documentos_para_probar = [11, 12, 14]

print("🧪 INICIANDO TESTS DE VALIDACIÓN\n")

for doc_id in documentos_para_probar:
    resultado = test_documento_completo(doc_id)
    print(f"\n🔗 URLs para documento {doc_id}:")
    print(f"   Ver: http://127.0.0.1:8000/documentos/{doc_id}/")
    print(f"   Editar: http://127.0.0.1:8000/documentos/editar/{doc_id}/")
    print("-" * 60)

print("\n🏁 TESTS COMPLETADOS")
