#!/usr/bin/env python3
"""
Script para pruebas manuales de documentos en Django Shell
Ejecutar con: python manage.py shell < tools/test_documento_manual.py
"""

from decimal import Decimal

from django.utils import timezone

from taller.models import *

print("🧪 PRUEBAS MANUALES DE DOCUMENTOS - BACKEND")
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
        cantidad=2,
        precio_unitario=Decimal("10000"),
        codigo="FIL001",
    )
    print(
        f"✅ Repuesto: {linea_rep.nombre} - Cantidad: {linea_rep.cantidad} - Precio: ${linea_rep.precio_unitario}"
    )

    # Servicio (sin IVA)
    linea_serv = LineaServicio.objects.create(
        documento=doc_cl,
        nombre="Cambio de aceite",
        cantidad=1,
        precio_unitario=Decimal("5000"),
    )
    print(
        f"✅ Servicio: {linea_serv.nombre} - Cantidad: {linea_serv.cantidad} - Precio: ${linea_serv.precio_unitario}"
    )

    # Otro servicio (sin IVA)
    linea_otro = LineaOtroServicio.objects.create(
        documento=doc_cl, nombre="Balanceo", cantidad=1, precio_cliente=Decimal("3000")
    )
    print(
        f"✅ Otro servicio: {linea_otro.nombre} - Precio cliente: ${linea_otro.precio_cliente}"
    )

    # Recalcular totales
    doc_cl.recalcular_totales()
    doc_cl.refresh_from_db()

    print("\n💰 TOTALES DOCUMENTO CL:")
    print(f"   Repuestos: ${doc_cl.total_repuestos}")
    print(f"   Servicios: ${doc_cl.total_servicios}")
    print(f"   Otros: ${doc_cl.total_otros}")
    print(f"   IVA (19%): ${doc_cl.iva}")
    print(f"   TOTAL: ${doc_cl.total_general}")

    # Verificar cálculos esperados
    expected_repuestos = Decimal("20000")  # 2 * 10000
    expected_servicios = Decimal("5000")  # 1 * 5000
    expected_otros = Decimal("3000")  # 1 * 3000
    expected_iva = Decimal("3800")  # 19% de 20000
    expected_total = Decimal("31800")  # 20000 + 5000 + 3000 + 3800

    print("\n✅ VERIFICACIÓN:")
    print(
        f"   Repuestos esperados: ${expected_repuestos} - Actual: ${doc_cl.total_repuestos} - {'✅' if doc_cl.total_repuestos == expected_repuestos else '❌'}"
    )
    print(
        f"   Servicios esperados: ${expected_servicios} - Actual: ${doc_cl.total_servicios} - {'✅' if doc_cl.total_servicios == expected_servicios else '❌'}"
    )
    print(
        f"   Otros esperados: ${expected_otros} - Actual: ${doc_cl.total_otros} - {'✅' if doc_cl.total_otros == expected_otros else '❌'}"
    )
    print(
        f"   IVA esperado: ${expected_iva} - Actual: ${doc_cl.iva} - {'✅' if doc_cl.iva == expected_iva else '❌'}"
    )
    print(
        f"   Total esperado: ${expected_total} - Actual: ${doc_cl.total_general} - {'✅' if doc_cl.total_general == expected_total else '❌'}"
    )

except Exception as e:
    print(f"❌ Error creando documento CL: {e}")

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
        cantidad=1,
        precio_unitario=Decimal("100"),
        codigo="BP001",
    )
    print(
        f"✅ Repuesto: {linea_rep_us.nombre} - Cantidad: {linea_rep_us.cantidad} - Precio: ${linea_rep_us.precio_unitario}"
    )

    # Servicio (sin IVA en US)
    linea_serv_us = LineaServicio.objects.create(
        documento=doc_us, nombre="Labor", cantidad=1, precio_unitario=Decimal("50")
    )
    print(
        f"✅ Servicio: {linea_serv_us.nombre} - Cantidad: {linea_serv_us.cantidad} - Precio: ${linea_serv_us.precio_unitario}"
    )

    # Recalcular totales
    doc_us.recalcular_totales()
    doc_us.refresh_from_db()

    print("\n💰 TOTALES DOCUMENTO US:")
    print(f"   Repuestos: ${doc_us.total_repuestos}")
    print(f"   Servicios: ${doc_us.total_servicios}")
    print(f"   Otros: ${doc_us.total_otros}")
    print(f"   Sales Tax (0%): ${doc_us.iva}")
    print(f"   TOTAL: ${doc_us.total_general}")

    # Verificar cálculos esperados
    expected_repuestos_us = Decimal("100")  # 1 * 100
    expected_servicios_us = Decimal("50")  # 1 * 50
    expected_otros_us = Decimal("0")  # Sin otros servicios
    expected_iva_us = Decimal("0")  # 0% en US
    expected_total_us = Decimal("150")  # 100 + 50 + 0 + 0

    print("\n✅ VERIFICACIÓN:")
    print(
        f"   Repuestos esperados: ${expected_repuestos_us} - Actual: ${doc_us.total_repuestos} - {'✅' if doc_us.total_repuestos == expected_repuestos_us else '❌'}"
    )
    print(
        f"   Servicios esperados: ${expected_servicios_us} - Actual: ${doc_us.total_servicios} - {'✅' if doc_us.total_servicios == expected_servicios_us else '❌'}"
    )
    print(
        f"   Otros esperados: ${expected_otros_us} - Actual: ${doc_us.total_otros} - {'✅' if doc_us.total_otros == expected_otros_us else '❌'}"
    )
    print(
        f"   Sales Tax esperado: ${expected_iva_us} - Actual: ${doc_us.iva} - {'✅' if doc_us.iva == expected_iva_us else '❌'}"
    )
    print(
        f"   Total esperado: ${expected_total_us} - Actual: ${doc_us.total_general} - {'✅' if doc_us.total_general == expected_total_us else '❌'}"
    )

except Exception as e:
    print(f"❌ Error creando documento US: {e}")

# 3. Verificar coherencia de datos
print("\n🔍 VERIFICANDO COHERENCIA DE DATOS")
print("-" * 40)

try:
    # Verificar que los documentos tienen los datos correctos
    print("📋 DOCUMENTO CL:")
    print(f"   Empresa: {doc_cl.empresa.nombre_taller} ({doc_cl.empresa.pais})")
    print(
        f"   Cliente: {doc_cl.cliente.nombre} (Empresa: {doc_cl.cliente.empresa.pais})"
    )
    print(
        f"   Vehículo: {doc_cl.vehiculo.patente} (Empresa: {doc_cl.vehiculo.empresa.pais})"
    )
    print(
        f"   Técnico: {doc_cl.tecnico_responsable.nombre} (Empresa: {doc_cl.tecnico_responsable.empresa.pais})"
    )

    print("\n📋 DOCUMENTO US:")
    print(f"   Empresa: {doc_us.empresa.nombre_taller} ({doc_us.empresa.pais})")
    print(
        f"   Cliente: {doc_us.cliente.nombre} (Empresa: {doc_us.cliente.empresa.pais})"
    )
    print(
        f"   Vehículo: {doc_us.vehiculo.patente} (Empresa: {doc_us.vehiculo.empresa.pais})"
    )
    print(
        f"   Técnico: {doc_us.tecnico_responsable.nombre} (Empresa: {doc_us.tecnico_responsable.empresa.pais})"
    )

    # Verificar coherencia
    cl_coherente = (
        doc_cl.empresa.pais == "CL"
        and doc_cl.cliente.empresa.pais == "CL"
        and doc_cl.vehiculo.empresa.pais == "CL"
        and doc_cl.tecnico_responsable.empresa.pais == "CL"
    )

    us_coherente = (
        doc_us.empresa.pais == "US"
        and doc_us.cliente.empresa.pais == "US"
        and doc_us.vehiculo.empresa.pais == "US"
        and doc_us.tecnico_responsable.empresa.pais == "US"
    )

    print("\n✅ COHERENCIA:")
    print(f"   Documento CL coherente: {'✅' if cl_coherente else '❌'}")
    print(f"   Documento US coherente: {'✅' if us_coherente else '❌'}")

except Exception as e:
    print(f"❌ Error verificando coherencia: {e}")

# 4. Verificar campos de auditoría
print("\n📝 VERIFICANDO CAMPOS DE AUDITORÍA")
print("-" * 40)

try:
    print("📋 DOCUMENTO CL:")
    print(f"   Created by: {doc_cl.created_by}")
    print(f"   Updated by: {doc_cl.updated_by}")
    print(f"   Created at: {doc_cl.created_at}")
    print(f"   Updated at: {doc_cl.updated_at}")

    print("\n📋 DOCUMENTO US:")
    print(f"   Created by: {doc_us.created_by}")
    print(f"   Updated by: {doc_us.updated_by}")
    print(f"   Created at: {doc_us.created_at}")
    print(f"   Updated at: {doc_us.updated_at}")

    # Verificar que los campos están completos
    cl_audit_ok = all(
        [doc_cl.created_by, doc_cl.updated_by, doc_cl.created_at, doc_cl.updated_at]
    )

    us_audit_ok = all(
        [doc_us.created_by, doc_us.updated_by, doc_us.created_at, doc_us.updated_at]
    )

    print("\n✅ AUDITORÍA:")
    print(f"   Documento CL completo: {'✅' if cl_audit_ok else '❌'}")
    print(f"   Documento US completo: {'✅' if us_audit_ok else '❌'}")

except Exception as e:
    print(f"❌ Error verificando auditoría: {e}")

# 5. Resumen final
print("\n" + "=" * 60)
print("📊 RESUMEN DE PRUEBAS MANUALES")
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
    cl_correcto = (
        doc_cl.total_repuestos == Decimal("20000")
        and doc_cl.total_servicios == Decimal("5000")
        and doc_cl.total_otros == Decimal("3000")
        and doc_cl.iva == Decimal("3800")
        and doc_cl.total_general == Decimal("31800")
    )

    us_correcto = (
        doc_us.total_repuestos == Decimal("100")
        and doc_us.total_servicios == Decimal("50")
        and doc_us.total_otros == Decimal("0")
        and doc_us.iva == Decimal("0")
        and doc_us.total_general == Decimal("150")
    )

    print("\n✅ RESULTADOS:")
    print(f"   Cálculos CL correctos: {'✅' if cl_correcto else '❌'}")
    print(f"   Cálculos US correctos: {'✅' if us_correcto else '❌'}")

    if cl_correcto and us_correcto:
        print("\n🎉 ¡TODAS LAS PRUEBAS MANUALES PASARON!")
        print("   El backend calcula correctamente los totales")
        print("   Los cálculos coinciden con el frontend")
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON")
        print("   Revisar los cálculos en el backend")

except Exception as e:
    print(f"❌ Error en resumen final: {e}")

print("\n" + "=" * 60)
print("🏁 PRUEBAS MANUALES COMPLETADAS")
print("=" * 60)
