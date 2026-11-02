"""
Test de validación de KPIs que compara kpi_helpers vs. agregación manual.
Blinda cambios futuros en los cálculos de KPIs.
"""

from decimal import Decimal

import pytest

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from taller.models import Cliente, Documento, Empresa, LineaServicio, Tecnico, Vehiculo
from taller.servicios.models import Servicio
from taller.utils.kpi_helpers import KPICalculator, get_kpi_tecnico_mes_actual


@pytest.mark.django_db
def test_kpi_tecnico_mes_actual_consistency():
    """Test que verifica consistencia entre kpi_helpers y agregación manual."""

    # Crear datos de prueba
    empresa = Empresa.objects.create(nombre_taller="Test Garage", pais="US", moneda="USD")
    tecnico = Tecnico.objects.create(empresa=empresa, nombre="Test Tech")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", rut_ein="12-3456789")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca="Ford",
        modelo="F-150",
        vin="VINTEST123",
    )

    # Crear servicio
    servicio = Servicio.objects.create(
        empresa=empresa,
        nombre="Test Service",
        descripcion="Test service description",
        precio=Decimal("100.00"),
    )

    # Crear documento del mes actual
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tecnico_responsable=tecnico,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
    )

    # Crear líneas de servicio
    LineaServicio.objects.create(
        documento=documento,
        servicio=servicio,
        cantidad=2,
        precio_unitario=Decimal("100.00"),
        descuento=Decimal("10.00"),  # 10% descuento
    )

    LineaServicio.objects.create(
        documento=documento,
        servicio=servicio,
        cantidad=1,
        precio_unitario=Decimal("50.00"),
        descuento=Decimal("0.00"),  # Sin descuento
    )

    # Calcular con kpi_helpers
    kpi_results = list(get_kpi_tecnico_mes_actual(empresa.id))

    # Calcular manualmente
    monto_manual = ExpressionWrapper(
        F("cantidad") * F("precio_unitario") * (1 - F("descuento") / 100),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    manual_results = list(
        LineaServicio.objects.filter(documento__fecha_emision__month=timezone.now().month)
        .filter(documento__empresa=empresa)
        .annotate(monto=monto_manual)
        .values("documento__tecnico_responsable__nombre")
        .annotate(total=Sum("monto"))
    )

    # Verificar consistencia
    assert len(kpi_results) == len(manual_results), "Número de resultados diferente"

    if kpi_results and manual_results:
        kpi_total = kpi_results[0]["total"]
        manual_total = manual_results[0]["total"]

        # Verificar que los totales coinciden (con tolerancia decimal)
        assert abs(kpi_total - manual_total) < Decimal(
            "0.01"
        ), f"Totales diferentes: {kpi_total} vs {manual_total}"

        # Verificar que el técnico es el mismo
        assert (
            kpi_results[0]["documento__tecnico_responsable__nombre"]
            == manual_results[0]["documento__tecnico_responsable__nombre"]
        )


@pytest.mark.django_db
def test_kpi_calculator_consistency():
    """Test que verifica consistencia del KPICalculator."""

    # Crear datos de prueba
    empresa = Empresa.objects.create(nombre_taller="Test Garage 2", pais="CL", moneda="CLP")
    tecnico = Tecnico.objects.create(empresa=empresa, nombre="Test Tech 2")
    cliente = Cliente.objects.create(
        empresa=empresa, nombre="Test Client 2", rut_ein="12.345.678-9"
    )
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST456",
        marca="Toyota",
        modelo="Corolla",
        vin="VINTEST456",
    )

    # Crear servicio
    servicio = Servicio.objects.create(
        empresa=empresa,
        nombre="Test Service 2",
        descripcion="Test service description 2",
        precio=Decimal("50000.00"),
    )

    # Crear documento del mes actual
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tecnico_responsable=tecnico,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
    )

    # Crear líneas de servicio
    LineaServicio.objects.create(
        documento=documento,
        servicio=servicio,
        cantidad=3,
        precio_unitario=Decimal("50000.00"),
        descuento=Decimal("5.00"),  # 5% descuento
    )

    # Usar KPICalculator
    calculator = KPICalculator(empresa.id)
    kpi_results = list(calculator.get_totales_por_tecnico())

    # Calcular manualmente
    monto_manual = ExpressionWrapper(
        F("cantidad") * F("precio_unitario") * (1 - F("descuento") / 100),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    manual_results = list(
        LineaServicio.objects.filter(documento__fecha_emision__month=timezone.now().month)
        .filter(documento__empresa=empresa)
        .annotate(monto=monto_manual)
        .values("documento__tecnico_responsable__nombre")
        .annotate(total=Sum("monto"))
    )

    # Verificar consistencia
    assert len(kpi_results) == len(manual_results), "Número de resultados diferente"

    if kpi_results and manual_results:
        kpi_total = kpi_results[0]["total"]
        manual_total = manual_results[0]["total"]

        # Verificar que los totales coinciden
        assert abs(kpi_total - manual_total) < Decimal(
            "0.01"
        ), f"Totales diferentes: {kpi_total} vs {manual_total}"


@pytest.mark.django_db
def test_kpi_documentos_por_estado_consistency():
    """Test que verifica consistencia de documentos por estado."""

    # Crear datos de prueba
    empresa = Empresa.objects.create(nombre_taller="Test Garage 3", pais="US", moneda="USD")
    tecnico = Tecnico.objects.create(empresa=empresa, nombre="Test Tech 3")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client 3", rut_ein="12-3456789")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST789",
        marca="Honda",
        modelo="Civic",
        vin="VINTEST789",
    )

    # Crear documentos con diferentes estados
    Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tecnico_responsable=tecnico,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        total=Decimal("100.00"),
    )

    Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tecnico_responsable=tecnico,
        tipo="OT",
        estado="emitido",
        fecha_emision=timezone.now().date(),
        total=Decimal("200.00"),
    )

    Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tecnico_responsable=tecnico,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
        total=Decimal("150.00"),
    )

    # Usar KPICalculator
    calculator = KPICalculator(empresa.id)
    kpi_results = list(calculator.get_documentos_por_estado())

    # Calcular manualmente
    manual_results = list(
        Documento.objects.filter(fecha_emision__month=timezone.now().month)
        .filter(empresa=empresa)
        .values("estado")
        .annotate(cantidad=Sum("id"), total_monto=Sum("total"))
    )

    # Verificar consistencia
    assert len(kpi_results) == len(manual_results), "Número de resultados diferente"

    # Verificar que los estados coinciden
    kpi_estados = {r["estado"] for r in kpi_results}
    manual_estados = {r["estado"] for r in manual_results}
    assert kpi_estados == manual_estados, f"Estados diferentes: {kpi_estados} vs {manual_estados}"


@pytest.mark.django_db
def test_kpi_helpers_monto_calculado():
    """Test que verifica el cálculo de monto en KPIHelpers."""

    from taller.utils.kpi_helpers import KPIHelpers

    # Crear datos de prueba
    empresa = Empresa.objects.create(nombre_taller="Test Garage 4", pais="CL", moneda="CLP")
    tecnico = Tecnico.objects.create(empresa=empresa, nombre="Test Tech 4")
    cliente = Cliente.objects.create(
        empresa=empresa, nombre="Test Client 4", rut_ein="12.345.678-9"
    )
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST000",
        marca="Nissan",
        modelo="Sentra",
        vin="VINTEST000",
    )

    # Crear servicio
    servicio = Servicio.objects.create(
        empresa=empresa,
        nombre="Test Service 4",
        descripcion="Test service description 4",
        precio=Decimal("100000.00"),
    )

    # Crear documento
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tecnico_responsable=tecnico,
        tipo="OT",
        estado="borrador",
        fecha_emision=timezone.now().date(),
    )

    # Crear línea de servicio con descuento
    linea = LineaServicio.objects.create(
        documento=documento,
        servicio=servicio,
        cantidad=2,
        precio_unitario=Decimal("100000.00"),
        descuento=Decimal("15.00"),  # 15% descuento
    )

    # Calcular monto esperado manualmente
    # cantidad * precio_unitario * (1 - descuento/100)
    # 2 * 100000 * (1 - 15/100) = 2 * 100000 * 0.85 = 170000
    monto_esperado = Decimal("170000.00")

    # Usar KPIHelpers
    monto_calculado = KPIHelpers.get_monto_calculado()

    # Aplicar el cálculo a la línea
    resultado = LineaServicio.objects.filter(id=linea.id).annotate(monto=monto_calculado).first()

    # Verificar que el cálculo es correcto
    assert abs(resultado.monto - monto_esperado) < Decimal(
        "0.01"
    ), f"Monto calculado incorrecto: {resultado.monto} vs {monto_esperado}"


if __name__ == "__main__":
    # Para ejecutar manualmente
    import os
    import sys

    import django

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
    django.setup()

    print("🧪 Ejecutando tests de validación de KPIs...")

    try:
        test_kpi_tecnico_mes_actual_consistency()
        print("✅ test_kpi_tecnico_mes_actual_consistency: PASSED")
    except Exception as e:
        print(f"❌ test_kpi_tecnico_mes_actual_consistency: FAILED - {e}")

    try:
        test_kpi_calculator_consistency()
        print("✅ test_kpi_calculator_consistency: PASSED")
    except Exception as e:
        print(f"❌ test_kpi_calculator_consistency: FAILED - {e}")

    try:
        test_kpi_documentos_por_estado_consistency()
        print("✅ test_kpi_documentos_por_estado_consistency: PASSED")
    except Exception as e:
        print(f"❌ test_kpi_documentos_por_estado_consistency: FAILED - {e}")

    try:
        test_kpi_helpers_monto_calculado()
        print("✅ test_kpi_helpers_monto_calculado: PASSED")
    except Exception as e:
        print(f"❌ test_kpi_helpers_monto_calculado: FAILED - {e}")

    print("🎯 Tests de validación de KPIs completados!")
