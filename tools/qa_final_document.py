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
    user_cl = User.objects.get(username="admin_chile")
    empresa_cl = user_cl.empresa

    # Obtener cliente, vehículo y técnico
    cliente_cl = empresa_cl.cliente_set.first()
    vehiculo_cl = empresa_cl.vehiculo_set.first()
    tecnico_cl = empresa_cl.tecnico_set.first()

    if not cliente_cl or not vehiculo_cl or not tecnico_cl:
        print("❌ Faltan datos básicos para Chile")
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

        # Agregar líneas
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

        print(f"✅ Documento CL creado: ID {doc_cl.id}")
        print(f"   Repuestos: ${doc_cl.total_repuestos}")
        print(f"   Servicios: ${doc_cl.total_servicios}")
        print(f"   Otros: ${doc_cl.total_otros}")
        print(f"   IVA: ${doc_cl.iva}")
        print(f"   Total: ${doc_cl.total_general}")

        # Verificar cálculos esperados
        expected_total = Decimal("31800")  # 20000 + 5000 + 3000 + 3800
        if doc_cl.total_general == expected_total:
            print("✅ Cálculos CL correctos")
        else:
            print(
                f"❌ Error en cálculos CL: esperado {expected_total}, obtenido {doc_cl.total_general}"
            )

except Exception as e:
    print(f"❌ Error en test CL: {e}")

# Test USA
print("\n2. CREANDO DOCUMENTO USA (USD + Sales Tax 0%)")
print("-" * 40)

try:
    # Obtener usuario y empresa USA
    user_us = User.objects.get(username="testuser_usa")
    empresa_us = user_us.empresa

    # Obtener cliente, vehículo y técnico
    cliente_us = empresa_us.cliente_set.first()
    vehiculo_us = empresa_us.vehiculo_set.first()
    tecnico_us = empresa_us.tecnico_set.first()

    if not cliente_us or not vehiculo_us or not tecnico_us:
        print("❌ Faltan datos básicos para USA")
    else:
        # Crear documento
        doc_us = Documento.objects.create(
            empresa=empresa_us,
            cliente=cliente_us,
            vehiculo=vehiculo_us,
            tecnico_responsable=tecnico_us,
            tipo="OT",
            fecha_emision=timezone.now(),
            created_by=user_us,
            updated_by=user_us,
        )

        # Agregar líneas
        LineaRepuesto.objects.create(
            documento=doc_us,
            nombre="Brake Pads",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("100.00"),
            descuento=Decimal("0"),
        )

        LineaServicio.objects.create(
            documento=doc_us,
            nombre="Oil Change",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("50.00"),
            descuento=Decimal("0"),
        )

        # Recalcular totales
        doc_us.recalcular_totales(save=True)
        doc_us.refresh_from_db()

        print(f"✅ Documento US creado: ID {doc_us.id}")
        print(f"   Repuestos: ${doc_us.total_repuestos}")
        print(f"   Servicios: ${doc_us.total_servicios}")
        print(f"   Otros: ${doc_us.total_otros}")
        print(f"   Sales Tax: ${doc_us.iva}")
        print(f"   Total: ${doc_us.total_general}")

        # Verificar cálculos esperados
        expected_total = Decimal("150.00")  # 100 + 50 + 0 (sin sales tax)
        if doc_us.total_general == expected_total:
            print("✅ Cálculos US correctos")
        else:
            print(
                f"❌ Error en cálculos US: esperado {expected_total}, obtenido {doc_us.total_general}"
            )

except Exception as e:
    print(f"❌ Error en test US: {e}")

print("\n=== QA FINAL COMPLETADO ===")
