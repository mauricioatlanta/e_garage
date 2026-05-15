from decimal import Decimal

from django.utils import timezone

from taller.models import *

print("Testing backend calculations...")

try:
    # Get CL company
    emp_cl = Empresa.objects.filter(pais="CL").first()
    if not emp_cl:
        print("No CL company found")
        exit(1)

    print(f"CL Company: {emp_cl.nombre_taller}")

    # Get basic data
    cli_cl = emp_cl.cliente_set.first()
    tec_cl = emp_cl.tecnicos.first()
    veh_cl = emp_cl.vehiculo_set.first()

    if not all([cli_cl, tec_cl, veh_cl]):
        print("Missing basic data")
        exit(1)

    # Create document
    doc_cl = Documento.objects.create(
        empresa=emp_cl,
        cliente=cli_cl,
        vehiculo=veh_cl,
        tecnico_responsable=tec_cl,
        tipo="OT",
        fecha_emision=timezone.now(),
    )

    print(f"Document created: ID {doc_cl.id}")

    # Add lines
    print("Adding lines...")

    # Repuesto
    linea_rep = LineaRepuesto.objects.create(
        documento=doc_cl,
        nombre="Filtro de aire",
        cantidad=Decimal("2"),
        precio_unitario=Decimal("10000"),
        codigo="FIL001",
    )
    print(f"Repuesto: {linea_rep.nombre} - Subtotal: ${linea_rep.subtotal}")

    # Servicio
    linea_serv = LineaServicio.objects.create(
        documento=doc_cl,
        nombre="Cambio de aceite",
        cantidad=Decimal("1"),
        precio_unitario=Decimal("5000"),
    )
    print(f"Servicio: {linea_serv.nombre} - Subtotal: ${linea_serv.subtotal}")

    # Recalculate totals
    print("Recalculating totals...")
    doc_cl.refresh_from_db()
    doc_cl.recalcular_totales()

    print("TOTALS CALCULATED:")
    print(f"  Repuestos: ${doc_cl.total_repuestos}")
    print(f"  Servicios: ${doc_cl.total_servicios}")
    print(f"  IVA (19%): ${doc_cl.iva}")
    print(f"  TOTAL: ${doc_cl.total_general}")

    # Expected calculations
    expected_repuestos = Decimal("20000")  # 2 * 10000
    expected_servicios = Decimal("5000")  # 1 * 5000
    expected_iva = Decimal("3800")  # 19% of 20000
    expected_total = Decimal("23800")  # 20000 + 5000 + 3800

    print("EXPECTED TOTALS:")
    print(f"  Repuestos: ${expected_repuestos}")
    print(f"  Servicios: ${expected_servicios}")
    print(f"  IVA (19%): ${expected_iva}")
    print(f"  TOTAL: ${expected_total}")

    # Verify coherence
    print("VERIFICATION:")
    rep_ok = doc_cl.total_repuestos == expected_repuestos
    serv_ok = doc_cl.total_servicios == expected_servicios
    iva_ok = doc_cl.iva == expected_iva
    total_ok = doc_cl.total_general == expected_total

    print(f"  Repuestos: {'OK' if rep_ok else 'ERROR'}")
    print(f"  Servicios: {'OK' if serv_ok else 'ERROR'}")
    print(f"  IVA: {'OK' if iva_ok else 'ERROR'}")
    print(f"  TOTAL: {'OK' if total_ok else 'ERROR'}")

    coherence_ok = all([rep_ok, serv_ok, iva_ok, total_ok])

    if coherence_ok:
        print("CALCULATIONS CORRECT!")
        print("Backend == Frontend confirmed")
    else:
        print("THERE ARE DISCREPANCIES")
        print("Review implementation")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()

print("Test completed")
