#!/usr/bin/env python3
"""
Script para probar las vistas ver_documento y editar_documento
después de implementar prefetch_related
"""

import os
import sys

import django

# Configurar Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


from taller.models.documento import Documento


def probar_vistas_documento():
    """Prueba las vistas de documento con datos reales"""
    print("🧪 PROBANDO VISTAS DE DOCUMENTO CON PREFETCH_RELATED")
    print("=" * 60)

    # Buscar un documento con líneas
    documento_con_lineas = None

    for documento in Documento.objects.all():
        total_lineas = (
            documento.lineas_repuesto.count()
            + documento.lineas_servicio.count()
            + documento.lineas_otro_servicio.count()
        )
        if total_lineas > 0:
            documento_con_lineas = documento
            break

    if not documento_con_lineas:
        print("❌ No se encontraron documentos con líneas para probar")
        return False

    print(f"📄 Probando con Documento #{documento_con_lineas.numero_documento}")
    print(f"   - ID: {documento_con_lineas.id}")
    print(f"   - Empresa: {documento_con_lineas.empresa.nombre_taller}")

    # Simular vista ver_documento
    print("\n1. Simulando vista ver_documento:")

    # Consulta como en la vista actualizada
    documento_optimizado = (
        Documento.objects.select_related("cliente", "vehiculo", "mecanico")
        .prefetch_related("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio")
        .get(id=documento_con_lineas.id)
    )

    repuestos = documento_optimizado.lineas_repuesto.all()
    servicios = documento_optimizado.lineas_servicio.all()
    otros_servicios = documento_optimizado.lineas_otro_servicio.all()

    print(f"   🔧 Repuestos encontrados: {repuestos.count()}")
    for rep in repuestos[:3]:
        precio_rep = getattr(rep, "precio_unitario", 0)
        cantidad_rep = getattr(rep, "cantidad", 1)
        nombre_rep = getattr(rep, "nombre", "Sin nombre")
        print(f"      - {nombre_rep}: ${precio_rep} x {cantidad_rep}")

    print(f"   🛠️  Servicios encontrados: {servicios.count()}")
    for serv in servicios[:3]:
        precio_serv = getattr(serv, "precio_unitario", 0)
        nombre_serv = getattr(serv, "nombre", "Sin nombre")
        print(f"      - {nombre_serv}: ${precio_serv}")

    print(f"   🏢 Otros servicios encontrados: {otros_servicios.count()}")
    for otro in otros_servicios[:3]:
        nombre_otro = getattr(otro, "nombre_servicio", "Sin nombre")
        precio_otro = getattr(otro, "precio_cliente", 0)
        empresa_otro = getattr(otro, "empresa_externa", "")
        print(f"      - {nombre_otro} ({empresa_otro}): ${precio_otro}")

    # Calcular totales como en la vista
    subtotal_repuestos = sum(
        getattr(r, "precio_unitario", 0) * getattr(r, "cantidad", 1) for r in repuestos
    )
    subtotal_servicios = sum(getattr(s, "precio_unitario", 0) for s in servicios)
    subtotal_otros_servicios = sum(getattr(o, "precio_cliente", 0) for o in otros_servicios)

    subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
    iva = subtotal * 0.19
    total = subtotal + iva

    print("\n2. Cálculos de totales:")
    print(f"   💰 Subtotal repuestos: ${subtotal_repuestos}")
    print(f"   💰 Subtotal servicios: ${subtotal_servicios}")
    print(f"   💰 Subtotal otros servicios: ${subtotal_otros_servicios}")
    print(f"   💰 Subtotal total: ${subtotal}")
    print(f"   💰 IVA (19%): ${iva}")
    print(f"   💰 TOTAL: ${total}")

    # Comparar con los métodos del modelo
    print("\n3. Comparación con métodos del modelo:")
    total_modelo = documento_optimizado.total_general()
    print(f"   📊 Total del modelo: ${total_modelo}")
    print(f"   ✅ Totales coinciden: {abs(float(total) - float(total_modelo)) < 0.01}")

    return True


if __name__ == "__main__":
    try:
        resultado = probar_vistas_documento()
        if resultado:
            print("\n🎉 PRUEBA DE VISTAS COMPLETADA EXITOSAMENTE")
        else:
            print("\n⚠️  PRUEBA DE VISTAS FALLÓ")
    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBA: {e}")
        import traceback

        traceback.print_exc()
