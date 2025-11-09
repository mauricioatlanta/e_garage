from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from taller.models import Documento, LineaOtroServicio, LineaRepuesto, LineaServicio

User = get_user_model()

print("=== QA FINAL - DOCUMENTO COMPLETO ===")

# Test Chile
print("\n1. CREANDO DOCUMENTO CHILE (CLP + IVA 19%)")
print("-" * 40)

try:
    # Obtener usuario y empresa Chile
    user_cl = User.objects.get(username="test_chile")
    empresa_cl = user_cl.empresa

    # Obtener cliente, vehiculo y tecnico
    cliente_cl = empresa_cl.cliente_set.first()
    vehiculo_cl = empresa_cl.vehiculo_set.first()
    tecnico_cl = empresa_cl.tecnicos.first()

    if not cliente_cl or not vehiculo_cl or not tecnico_cl:
        print("ERROR: Faltan datos basicos para Chile")
    else:
        # Crear documento
        doc_cl = Documento.objects.create(
            empresa=empresa_cl,
            cliente=cliente_cl,
            vehiculo=vehiculo_cl,
            tecnico_responsable=tecnico_cl,
            tipo="OT",
            fecha_emision=timezone.now(),
            created_by=user_cl,
            updated_by=user_cl,
        )

        # Agregar lineas
        LineaRepuesto.objects.create(
            documento=doc_cl,
            nombre="Filtro de Aire",
            cantidad=Decimal("2"),
            precio_unitario=Decimal("10000"),
            descuento=Decimal("0"),
        )

        LineaServicio.objects.create(
            documento=doc_cl,
            nombre="Cambio de Aceite",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("5000"),
            descuento=Decimal("0"),
        )

        LineaOtroServicio.objects.create(
            documento=doc_cl,
            nombre="Balanceo",
            cantidad=Decimal("1"),
            costo_interno=Decimal("2000"),
            precio_cliente=Decimal("3000"),
        )

        # Recalcular totales
        doc_cl.recalcular_totales(save=True)
        doc_cl.refresh_from_db()

        print(f"OK: Documento CL creado: ID {doc_cl.id}")
        print(f"   Repuestos: ${doc_cl.total_repuestos}")
        print(f"   Servicios: ${doc_cl.total_servicios}")
        print(f"   Otros: ${doc_cl.total_otros}")
        print(f"   IVA: ${doc_cl.iva}")
        print(f"   Total: ${doc_cl.total_general}")

        # Verificar calculos esperados
        expected_total = Decimal("31800")  # 20000 + 5000 + 3000 + 3800
        if doc_cl.total_general == expected_total:
            print("OK: Calculos CL correctos")
        else:
            print(
                f"ERROR: Calculos CL incorrectos: esperado {expected_total}, obtenido {doc_cl.total_general}"
            )

except Exception as e:
    print(f"ERROR en test CL: {e}")

print("\n=== QA FINAL COMPLETADO ===")
