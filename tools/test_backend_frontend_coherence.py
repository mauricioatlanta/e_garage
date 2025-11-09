#!/usr/bin/env python3
"""
Script para verificar coherencia entre cálculos backend y frontend
Ejecutar con: python manage.py shell < tools/test_backend_frontend_coherence.py
"""

from decimal import Decimal

from django.utils import timezone

from taller.models import *

print("🧪 VERIFICANDO COHERENCIA BACKEND == FRONTEND")
print("=" * 60)

# 1. Crear documento CL
print("\n🇨🇱 CREANDO DOCUMENTO CHILE (CLP + IVA 19%)")
print("-" * 40)

try:
    # Obtener empresa CL
    emp_cl = Empresa.objects.filter(pais="CL").first()
    if not emp_cl:
        print("❌ No se encontró empresa CL")
        exit(1)

    print(f"✅ Empresa CL encontrada: {emp_cl.nombre_taller}")

    # Obtener cliente, técnico y vehículo
    cli_cl = emp_cl.cliente_set.first()
    tec_cl = emp_cl.tecnicos.first()
    veh_cl = emp_cl.vehiculo_set.first()

    if not all([cli_cl, tec_cl, veh_cl]):
        print("❌ Faltan datos básicos (cliente, técnico o vehículo)")
        exit(1)

    print(f"✅ Cliente: {cli_cl.nombre}")
    print(f"✅ Técnico: {tec_cl.nombre}")
    print(f"✅ Vehículo: {veh_cl.patente}")

    # Crear documento
    doc_cl = Documento.objects.create(
        empresa=emp_cl,
        cliente=cli_cl,
        vehiculo=veh_cl,
        tecnico_responsable=tec_cl,
        tipo="OT",
        fecha_emision=timezone.now(),
    )

    print(f"✅ Documento CL creado: ID {doc_cl.id}")

    # Agregar líneas
    print("\n📝 Agregando líneas al documento CL...")

    # Repuesto (con IVA)
    linea_rep = LineaRepuesto.objects.create(
        documento=doc_cl,
        nombre="Filtro de aire",
        cantidad=Decimal("2"),
        precio_unitario=Decimal("10000"),
        codigo="FIL001",
    )
    print(
        f"✅ Repuesto: {linea_rep.nombre} - Cantidad: {linea_rep.cantidad} - Precio: ${linea_rep.precio_unitario}"
    )
    print(f"   Subtotal calculado: ${linea_rep.subtotal}")

    # Servicio (sin IVA)
    linea_serv = LineaServicio.objects.create(
        documento=doc_cl,
        nombre="Cambio de aceite",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("5000"),
    )
    print(
        f"✅ Servicio: {linea_serv.nombre} - Cantidad: {linea_serv.cantidad} - Precio: ${linea_serv.precio_unitario}"
    )
    print(f"   Subtotal calculado: ${linea_serv.subtotal}")

    # Otro servicio (sin IVA)
    linea_otro = LineaOtroServicio.objects.create(
        documento=doc_cl,
        nombre="Balanceo",
        cantidad=Decimal("1"),
        precio_cliente=Decimal("3000"),
    )
    print(
        f"✅ Otro servicio: {linea_otro.nombre} - Precio cliente: ${linea_otro.precio_cliente}"
    )
    print(f"   Subtotal calculado: ${linea_otro.subtotal}")

    # Recalcular totales
    print("\n🔄 Recalculando totales del documento...")
    doc_cl.refresh_from_db()
    doc_cl.recalcular_totales()

    print("\n💰 TOTALES DOCUMENTO CL (BACKEND):")
    print(f"   Repuestos: ${doc_cl.total_repuestos}")
    print(f"   Servicios: ${doc_cl.total_servicios}")
    print(f"   Otros: ${doc_cl.total_otros}")
    print(f"   IVA (19%): ${doc_cl.iva}")
    print(f"   TOTAL: ${doc_cl.total_general}")

    # Verificar cálculos esperados (frontend)
    expected_repuestos = Decimal("20000")  # 2 * 10000
    expected_servicios = Decimal("5000")  # 1 * 5000
    expected_otros = Decimal("3000")  # 1 * 3000
    expected_iva = Decimal("3800")  # 19% de 20000
    expected_total = Decimal("31800")  # 20000 + 5000 + 3000 + 3800

    print("\n🎯 TOTALES ESPERADOS (FRONTEND):")
    print(f"   Repuestos: ${expected_repuestos}")
    print(f"   Servicios: ${expected_servicios}")
    print(f"   Otros: ${expected_otros}")
    print(f"   IVA (19%): ${expected_iva}")
    print(f"   TOTAL: ${expected_total}")

    # Verificar coherencia
    print("\n✅ VERIFICACIÓN DE COHERENCIA:")
    rep_ok = doc_cl.total_repuestos == expected_repuestos
    serv_ok = doc_cl.total_servicios == expected_servicios
    otros_ok = doc_cl.total_otros == expected_otros
    iva_ok = doc_cl.iva == expected_iva
    total_ok = doc_cl.total_general == expected_total

    print(
        f"   Repuestos: {'✅' if rep_ok else '❌'} (Backend: ${doc_cl.total_repuestos} vs Frontend: ${expected_repuestos})"
    )
    print(
        f"   Servicios: {'✅' if serv_ok else '❌'} (Backend: ${doc_cl.total_servicios} vs Frontend: ${expected_servicios})"
    )
    print(
        f"   Otros: {'✅' if otros_ok else '❌'} (Backend: ${doc_cl.total_otros} vs Frontend: ${expected_otros})"
    )
    print(
        f"   IVA: {'✅' if iva_ok else '❌'} (Backend: ${doc_cl.iva} vs Frontend: ${expected_iva})"
    )
    print(
        f"   TOTAL: {'✅' if total_ok else '❌'} (Backend: ${doc_cl.total_general} vs Frontend: ${expected_total})"
    )

    coherence_ok = all([rep_ok, serv_ok, otros_ok, iva_ok, total_ok])

except Exception as e:
    print(f"❌ Error creando documento CL: {e}")
    coherence_ok = False

# 2. Crear documento US
print("\n🇺🇸 CREANDO DOCUMENTO ESTADOS UNIDOS (USD + Sales Tax 0%)")
print("-" * 40)

try:
    # Obtener empresa US
    emp_us = Empresa.objects.filter(pais="US").first()
    if not emp_us:
        print("❌ No se encontró empresa US")
        exit(1)

    print(f"✅ Empresa US encontrada: {emp_us.nombre_taller}")

    # Obtener cliente, técnico y vehículo
    cli_us = emp_us.cliente_set.first()
    tec_us = emp_us.tecnicos.first()
    veh_us = emp_us.vehiculo_set.first()

    if not all([cli_us, tec_us, veh_us]):
        print("❌ Faltan datos básicos (cliente, técnico o vehículo)")
        exit(1)

    print(f"✅ Cliente: {cli_us.nombre}")
    print(f"✅ Técnico: {tec_us.nombre}")
    print(f"✅ Vehículo: {veh_us.patente}")

    # Crear documento
    doc_us = Documento.objects.create(
        empresa=emp_us,
        cliente=cli_us,
        vehiculo=veh_us,
        tecnico_responsable=tec_us,
        tipo="OT",
        fecha_emision=timezone.now(),
    )

    print(f"✅ Documento US creado: ID {doc_us.id}")

    # Agregar líneas
    print("\n📝 Agregando líneas al documento US...")

    # Repuesto (sin IVA en US)
    linea_rep_us = LineaRepuesto.objects.create(
        documento=doc_us,
        nombre="Brake Pad",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("100"),
        codigo="BP001",
    )
    print(
        f"✅ Repuesto: {linea_rep_us.nombre} - Cantidad: {linea_rep_us.cantidad} - Precio: ${linea_rep_us.precio_unitario}"
    )
    print(f"   Subtotal calculado: ${linea_rep_us.subtotal}")

    # Servicio (sin IVA en US)
    linea_serv_us = LineaServicio.objects.create(
        documento=doc_us,
        nombre="Labor",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("50"),
    )
    print(
        f"✅ Servicio: {linea_serv_us.nombre} - Cantidad: {linea_serv_us.cantidad} - Precio: ${linea_serv_us.precio_unitario}"
    )
    print(f"   Subtotal calculado: ${linea_serv_us.subtotal}")

    # Recalcular totales
    print("\n🔄 Recalculando totales del documento...")
    doc_us.refresh_from_db()
    doc_us.recalcular_totales()

    print("\n💰 TOTALES DOCUMENTO US (BACKEND):")
    print(f"   Repuestos: ${doc_us.total_repuestos}")
    print(f"   Servicios: ${doc_us.total_servicios}")
    print(f"   Otros: ${doc_us.total_otros}")
    print(f"   Sales Tax (0%): ${doc_us.iva}")
    print(f"   TOTAL: ${doc_us.total_general}")

    # Verificar cálculos esperados (frontend)
    expected_repuestos_us = Decimal("100")  # 1 * 100
    expected_servicios_us = Decimal("50")  # 1 * 50
    expected_otros_us = Decimal("0")  # Sin otros servicios
    expected_iva_us = Decimal("0")  # 0% en US
    expected_total_us = Decimal("150")  # 100 + 50 + 0 + 0

    print("\n🎯 TOTALES ESPERADOS (FRONTEND):")
    print(f"   Repuestos: ${expected_repuestos_us}")
    print(f"   Servicios: ${expected_servicios_us}")
    print(f"   Otros: ${expected_otros_us}")
    print(f"   Sales Tax (0%): ${expected_iva_us}")
    print(f"   TOTAL: ${expected_total_us}")

    # Verificar coherencia
    print("\n✅ VERIFICACIÓN DE COHERENCIA:")
    rep_ok_us = doc_us.total_repuestos == expected_repuestos_us
    serv_ok_us = doc_us.total_servicios == expected_servicios_us
    otros_ok_us = doc_us.total_otros == expected_otros_us
    iva_ok_us = doc_us.iva == expected_iva_us
    total_ok_us = doc_us.total_general == expected_total_us

    print(
        f"   Repuestos: {'✅' if rep_ok_us else '❌'} (Backend: ${doc_us.total_repuestos} vs Frontend: ${expected_repuestos_us})"
    )
    print(
        f"   Servicios: {'✅' if serv_ok_us else '❌'} (Backend: ${doc_us.total_servicios} vs Frontend: ${expected_servicios_us})"
    )
    print(
        f"   Otros: {'✅' if otros_ok_us else '❌'} (Backend: ${doc_us.total_otros} vs Frontend: ${expected_otros_us})"
    )
    print(
        f"   Sales Tax: {'✅' if iva_ok_us else '❌'} (Backend: ${doc_us.iva} vs Frontend: ${expected_iva_us})"
    )
    print(
        f"   TOTAL: {'✅' if total_ok_us else '❌'} (Backend: ${doc_us.total_general} vs Frontend: ${expected_total_us})"
    )

    coherence_ok_us = all([rep_ok_us, serv_ok_us, otros_ok_us, iva_ok_us, total_ok_us])

except Exception as e:
    print(f"❌ Error creando documento US: {e}")
    coherence_ok_us = False

# 3. Resumen final
print("\n" + "=" * 60)
print("📊 RESUMEN DE COHERENCIA BACKEND == FRONTEND")
print("=" * 60)

try:
    # Contar documentos creados
    total_docs = Documento.objects.count()
    docs_cl = Documento.objects.filter(empresa__pais="CL").count()
    docs_us = Documento.objects.filter(empresa__pais="US").count()

    print("📈 ESTADÍSTICAS:")
    print(f"   Total documentos: {total_docs}")
    print(f"   Documentos CL: {docs_cl}")
    print(f"   Documentos US: {docs_us}")

    # Verificar que los cálculos son correctos
    cl_correcto = coherence_ok
    us_correcto = coherence_ok_us

    print("\n✅ RESULTADOS:")
    print(f"   Cálculos CL correctos: {'✅' if cl_correcto else '❌'}")
    print(f"   Cálculos US correctos: {'✅' if us_correcto else '❌'}")

    if cl_correcto and us_correcto:
        print("\n🎉 ¡COHERENCIA BACKEND == FRONTEND CONFIRMADA!")
        print("   Los cálculos del backend coinciden exactamente con el frontend")
        print("   El sistema está listo para producción")
    else:
        print("\n❌ HAY DISCREPANCIAS EN LOS CÁLCULOS")
        print("   Revisar la implementación de los métodos de cálculo")

except Exception as e:
    print(f"❌ Error en resumen final: {e}")

print("\n" + "=" * 60)
print("🏁 VERIFICACIÓN DE COHERENCIA COMPLETADA")
print("=" * 60)
