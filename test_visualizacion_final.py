import os
import sys

import django

sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio


def test_final_visualizacion():
    """Test final para verificar que los datos se muestran correctamente"""

    print("🔍 TEST FINAL: Visualización de Documentos")
    print("=" * 60)

    # Verificar documento F-882
    try:
        documento = Documento.objects.get(numero_documento="F-882")

        print(f"📋 DOCUMENTO F-882 (ID: {documento.id})")
        print(f"   Cliente: {documento.cliente.nombre}")
        print(f"   Vehículo: {documento.vehiculo.patente}")
        print(f"   Empresa: {documento.empresa.nombre_taller}")

        # Verificar repuestos usando consulta directa
        repuestos = LineaRepuesto.objects.filter(documento=documento)
        print(f"\n🔩 REPUESTOS ({repuestos.count()}):")
        for rep in repuestos:
            precio_r = getattr(rep, "precio_unitario", getattr(rep, "precio", 0))
            subtotal_r = getattr(
                rep, "subtotal", precio_r * getattr(rep, "cantidad", 1)
            )
            print(f"   - {rep.codigo}: {rep.nombre}")
            print(f"     Cantidad: {rep.cantidad}, Precio: ${precio_r}")
            print(f"     Total: ${subtotal_r}")

        # Verificar servicios usando consulta directa
        servicios = LineaServicio.objects.filter(documento=documento)
        print(f"\n⚙️ SERVICIOS ({servicios.count()}):")
        for serv in servicios:
            precio_s = getattr(serv, "precio_unitario", getattr(serv, "precio", 0))
            print(f"   - {serv.nombre}: ${precio_s}")

        # Calcular totales
        total_repuestos = sum(
            getattr(
                r,
                "subtotal",
                getattr(r, "precio_unitario", getattr(r, "precio", 0))
                * getattr(r, "cantidad", 1),
            )
            for r in repuestos
        )
        total_servicios = sum(
            getattr(s, "precio_unitario", getattr(s, "precio", 0)) for s in servicios
        )
        subtotal = total_repuestos + total_servicios
        iva = subtotal * 0.19
        total_con_iva = subtotal + iva

        print(f"\n💰 CÁLCULOS:")
        print(f"   Subtotal repuestos: ${total_repuestos}")
        print(f"   Subtotal servicios: ${total_servicios}")
        print(f"   Subtotal total: ${subtotal}")
        print(f"   IVA (19%): ${iva:.0f}")
        print(f"   TOTAL CON IVA: ${total_con_iva:.0f}")

        # Verificar si el problema es con related_name
        print(f"\n🔗 TESTING RELATED_NAME:")
        try:
            repuestos_related = documento.repuestos.all()
            print(
                f"   ✅ documento.repuestos.all() funciona: {repuestos_related.count()} items"
            )
        except Exception as e:
            print(f"   ❌ documento.repuestos.all() falla: {e}")

        try:
            servicios_related = documento.servicios.all()
            print(
                f"   ✅ documento.servicios.all() funciona: {servicios_related.count()} items"
            )
        except Exception as e:
            print(f"   ❌ documento.servicios.all() falla: {e}")

        # URLs de testing
        print(f"\n🌐 URLs PARA VERIFICACIÓN MANUAL:")
        print(f"   📄 Ver documento: http://127.0.0.1:8000/documentos/{documento.id}/")
        print(
            f"   ✏️ Editar documento: http://127.0.0.1:8000/documentos/editar/{documento.id}/"
        )

        # Estado esperado vs real
        print(f"\n📊 RESUMEN:")
        if repuestos.exists():
            print(f"   ✅ Documento TIENE repuestos en BD")
        else:
            print(f"   ❌ Documento NO TIENE repuestos en BD")

        if servicios.exists():
            print(f"   ✅ Documento TIENE servicios en BD")
        else:
            print(f"   ❌ Documento NO TIENE servicios en BD")

        return True

    except Documento.DoesNotExist:
        print("❌ Documento F-882 no existe")
        return False


def verificar_otros_documentos():
    """Verificar otros documentos para comparación"""

    print(f"\n🔍 VERIFICANDO OTROS DOCUMENTOS CON DATOS:")

    # Buscar documentos con repuestos
    documentos_con_repuestos = []
    for doc in Documento.objects.all():
        repuestos_count = LineaRepuesto.objects.filter(documento=doc).count()
        if repuestos_count > 0:
            documentos_con_repuestos.append((doc, repuestos_count))

    print(f"📊 DOCUMENTOS CON REPUESTOS ({len(documentos_con_repuestos)}):")
    for doc, count in documentos_con_repuestos:
        print(f"   - {doc.numero_documento}: {count} repuestos")
        print(f"     URL: http://127.0.0.1:8000/documentos/{doc.id}/")


if __name__ == "__main__":
    test_final_visualizacion()
    verificar_otros_documentos()
