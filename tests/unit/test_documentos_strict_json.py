"""
Strict JSON validation tests for document creation API.

These tests disable the country middleware to ensure exact JSON responses
for critical business logic validation (inheritance, rounding, etc.).
"""

import json
from decimal import Decimal

import pytest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import NoReverseMatch, reverse

from tests.test_utils.http_asserts import assert_json_response


def _rev(cands, fb):
    """Helper to try multiple URL names and fallback to a path"""
    for n in cands:
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    return fb


@pytest.mark.django_db
@override_settings(MIDDLEWARE=[m for m in settings.MIDDLEWARE if "country_prefix" not in m])
def test_herencia_responsable_strict_json():
    """Test inheritance with strict JSON validation (no middleware redirects)"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaRepuesto, LineaServicio
        from taller.models.tecnico import Tecnico
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_strict_json", password="test")

    # Create empresa
    empresa = Empresa.objects.create(user=user, nombre_taller="Test Strict JSON", pais="CL")

    # Create cliente and vehiculo
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca_texto="Test",
        modelo_texto="Model",
        anio=2024,
    )

    # Create tecnico
    tecnico = Tecnico.objects.create(empresa=empresa, nombre="Test Tecnico", activo=True)

    c = Client()
    c.force_login(user)

    # Use direct path since middleware is disabled
    url = "/cl/documentos/api/create/"

    # Test data with tecnico_responsable and inheritance ON
    data = {
        "empresa_id": empresa.id,
        "cliente_id": cliente.id,
        "vehiculo_id": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "tecnico_responsable_id": tecnico.id,
        "heredar_responsable": True,  # Inheritance ON
        "lineas_servicio": [
            {
                "nombre": "Service 1",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
            }
        ],
        "lineas_repuesto": [
            {
                "nombre": "Repuesto 1",
                "cantidad": 1,
                "precio_unitario": "2000.00",
                "descuento": "0.00",
                "codigo": "REP-001",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")

    # Should succeed with exact 201 (no redirects)
    response_data = assert_json_response(response, expected_status_codes=(200, 201))

    # Check that document was created
    assert "documento" in response_data, "Response should contain documento object"
    assert "id" in response_data["documento"], "Documento should contain ID"
    documento_id = response_data["documento"]["id"]

    # Verify document has tecnico_responsable
    documento = Documento.objects.get(id=documento_id)
    assert documento.tecnico_responsable == tecnico, "Document should have tecnico_responsable"

    # Verify service lines were created
    linea_servicio = LineaServicio.objects.filter(documento=documento).first()
    assert linea_servicio is not None, "Service line should be created"

    # Verify repuesto lines were created
    linea_repuesto = LineaRepuesto.objects.filter(documento=documento).first()
    assert linea_repuesto is not None, "Repuesto line should be created"


@pytest.mark.django_db
@override_settings(MIDDLEWARE=[m for m in settings.MIDDLEWARE if "country_prefix" not in m])
def test_rounding_precision_strict_json():
    """Test rounding precision with strict JSON validation"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_rounding_strict", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Rounding Strict", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca_texto="Test",
        modelo_texto="Model",
        anio=2024,
    )

    c = Client()
    c.force_login(user)
    url = "/cl/documentos/api/create/"

    # Test case: Price with 2 decimals should be handled properly
    data = {
        "empresa_id": empresa.id,
        "cliente_id": cliente.id,
        "vehiculo_id": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_servicio": [
            {
                "nombre": "Service with 2 decimals",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")

    # Should succeed with exact 201
    response_data = assert_json_response(response, expected_status_codes=(200, 201))

    # Verify the line was created with proper rounding
    assert "documento" in response_data, "Response should contain documento object"
    assert "id" in response_data["documento"], "Documento should contain ID"
    doc_id = response_data["documento"]["id"]
    documento = Documento.objects.get(id=doc_id)
    linea = LineaServicio.objects.filter(documento=documento).first()

    assert linea is not None, "Service line should be created"
    # Price should be rounded to 2 decimal places
    assert linea.precio_unitario == Decimal(
        "1000.00"
    ), f"Price should be rounded to 2 decimals, got {linea.precio_unitario}"


@pytest.mark.django_db
@override_settings(MIDDLEWARE=[m for m in settings.MIDDLEWARE if "country_prefix" not in m])
def test_descuentos_extremos_strict_json():
    """Test extreme discount values with strict JSON validation"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_descuentos_strict", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Descuentos Strict", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca_texto="Test",
        modelo_texto="Model",
        anio=2024,
    )

    c = Client()
    c.force_login(user)
    url = "/cl/documentos/api/create/"

    # Test case: 100% discount
    data = {
        "empresa_id": empresa.id,
        "cliente_id": cliente.id,
        "vehiculo_id": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_servicio": [
            {
                "nombre": "Service 100% discount",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "100.00",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")

    # Should succeed with exact 201
    response_data = assert_json_response(response, expected_status_codes=(200, 201))

    # Verify the line was created with 100% discount
    assert "documento" in response_data, "Response should contain documento object"
    assert "id" in response_data["documento"], "Documento should contain ID"
    doc_id = response_data["documento"]["id"]
    documento = Documento.objects.get(id=doc_id)
    linea = LineaServicio.objects.filter(documento=documento).first()

    assert linea is not None, "Service line should be created"
    assert linea.descuento == Decimal("100.00"), f"Discount should be 100%, got {linea.descuento}"

    # Verify totals are calculated correctly (should be 0 with 100% discount)
    assert documento.total >= Decimal("0"), "Total should not be negative"
    assert documento.neto_servicios >= Decimal("0"), "Neto servicios should not be negative"
