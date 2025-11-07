#!/usr/bin/env python3
"""
Script simple para probar los cálculos del backend
Ejecutar con: python manage.py shell -c "exec(open('tools/test_backend_calculations.py').read())"
"""

from taller.models import *
from django.utils import timezone
from decimal import Decimal

print("🧪 PROBANDO CÁLCULOS DEL BACKEND")
print("=" * 50)

try:
    # Obtener empresa CL
    emp_cl = Empresa.objects.filter(pais="CL").first()
    if not emp_cl:
        print("❌ No se encontró empresa CL")
        exit(1)
    
    print(f"✅ Empresa CL: {emp_cl.nombre_taller}")
    
    # Obtener datos básicos
    cli_cl = emp_cl.cliente_set.first()
    tec_cl = emp_cl.tecnicos.first()
    veh_cl = emp_cl.vehiculo_set.first()
    
    if not all([cli_cl, tec_cl, veh_cl]):
        print("❌ Faltan datos básicos")
        exit(1)
    
    # Crear documento
    doc_cl = Documento.objects.create(
        empresa=emp_cl,
        cliente=cli_cl,
        vehiculo=veh_cl,
        tecnico_responsable=tec_cl,
        tipo="OT",
        fecha_emision=timezone.now()
    )
    
    print(f"✅ Documento creado: ID {doc_cl.id}")
    
    # Agregar líneas
    print("\n📝 Agregando líneas...")
    
    # Repuesto
    linea_rep = LineaRepuesto.objects.create(
        documento=doc_cl,
        nombre="Filtro de aire",
        cantidad=Decimal("2"),
        precio_unitario=Decimal("10000"),
        codigo="FIL001"
    )
    print(f"✅ Repuesto: {linea_rep.nombre} - Subtotal: ${linea_rep.subtotal}")
    
    # Servicio
    linea_serv = LineaServicio.objects.create(
        documento=doc_cl,
        nombre="Cambio de aceite",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("5000")
    )
    print(f"✅ Servicio: {linea_serv.nombre} - Subtotal: ${linea_serv.subtotal}")
    
    # Otro servicio
    linea_otro = LineaOtroServicio.objects.create(
        documento=doc_cl,
        nombre="Balanceo",
        cantidad=Decimal("1"),
        precio_cliente=Decimal("3000")
    )
    print(f"✅ Otro servicio: {linea_otro.nombre} - Subtotal: ${linea_otro.subtotal}")
    
    # Recalcular totales
    print("\n🔄 Recalculando totales...")
    doc_cl.refresh_from_db()
    doc_cl.recalcular_totales()
    
    print(f"\n💰 TOTALES CALCULADOS:")
    print(f"   Repuestos: ${doc_cl.total_repuestos}")
    print(f"   Servicios: ${doc_cl.total_servicios}")
    print(f"   Otros: ${doc_cl.total_otros}")
    print(f"   IVA (19%): ${doc_cl.iva}")
    print(f"   TOTAL: ${doc_cl.total_general}")
    
    # Verificar cálculos esperados
    expected_repuestos = Decimal("20000")  # 2 * 10000
    expected_servicios = Decimal("5000")   # 1 * 5000
    expected_otros = Decimal("3000")       # 1 * 3000
    expected_iva = Decimal("3800")         # 19% de 20000
    expected_total = Decimal("31800")      # 20000 + 5000 + 3000 + 3800
    
    print(f"\n🎯 TOTALES ESPERADOS:")
    print(f"   Repuestos: ${expected_repuestos}")
    print(f"   Servicios: ${expected_servicios}")
    print(f"   Otros: ${expected_otros}")
    print(f"   IVA (19%): ${expected_iva}")
    print(f"   TOTAL: ${expected_total}")
    
    # Verificar coherencia
    print(f"\n✅ VERIFICACIÓN:")
    rep_ok = doc_cl.total_repuestos == expected_repuestos
    serv_ok = doc_cl.total_servicios == expected_servicios
    otros_ok = doc_cl.total_otros == expected_otros
    iva_ok = doc_cl.iva == expected_iva
    total_ok = doc_cl.total_general == expected_total
    
    print(f"   Repuestos: {'✅' if rep_ok else '❌'}")
    print(f"   Servicios: {'✅' if serv_ok else '❌'}")
    print(f"   Otros: {'✅' if otros_ok else '❌'}")
    print(f"   IVA: {'✅' if iva_ok else '❌'}")
    print(f"   TOTAL: {'✅' if total_ok else '❌'}")
    
    coherence_ok = all([rep_ok, serv_ok, otros_ok, iva_ok, total_ok])
    
    if coherence_ok:
        print(f"\n🎉 ¡CÁLCULOS CORRECTOS!")
        print(f"   Backend == Frontend confirmado")
    else:
        print(f"\n❌ HAY DISCREPANCIAS")
        print(f"   Revisar implementación")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("🏁 PRUEBA COMPLETADA")
