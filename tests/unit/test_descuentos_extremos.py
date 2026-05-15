"""
Test extreme discount scenarios for repuestos and servicios.

These tests validate that extreme discount values (0%, 100%) are handled
correctly and that totals, subtotals, and taxes are calculated properly
without negative values.
"""

import json
from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import NoReverseMatch, reverse

from tests.test_utils.http_asserts import assert_json_response, assert_ok_or_redirect


def _rev(cands, fb):
    """Helper to try multiple URL names and fallback to a path"""
    for n in cands:
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    return fb


@pytest.mark.django_db
def test_descuento_0_porciento_servicios():
    """Test 0% discount on servicios - should have no discount effect"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_descuento_0", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Descuento 0", pais="CL")
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
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Test with 0% discount
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_servicio": [
            {
                "nombre": "Service 0% discount",
                "cantidad": 2,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])
        linea = LineaServicio.objects.filter(documento=documento).first()

        # Verify discount is 0%
        assert linea.descuento == Decimal("0.00"), f"Discount should be 0%, got {linea.descuento}"

        # Verify totals are calculated correctly (no discount effect)
        expected_subtotal = Decimal("2000.00")  # 2 * 1000.00
        assert (
            documento.neto_servicios == expected_subtotal
        ), f"Neto servicios should be {expected_subtotal}, got {documento.neto_servicios}"
        assert (
            documento.total >= expected_subtotal
        ), f"Total should be at least {expected_subtotal}, got {documento.total}"
        assert documento.total >= Decimal("0"), "Total should not be negative"


@pytest.mark.django_db
def test_descuento_100_porciento_servicios():
    """Test 100% discount on servicios - should result in 0 neto"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_descuento_100", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Descuento 100", pais="CL")
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
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Test with 100% discount
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
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
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])
        linea = LineaServicio.objects.filter(documento=documento).first()

        # Verify discount is 100%
        assert linea.descuento == Decimal(
            "100.00"
        ), f"Discount should be 100%, got {linea.descuento}"

        # Verify neto servicios is 0 (100% discount)
        assert documento.neto_servicios == Decimal(
            "0.00"
        ), f"Neto servicios should be 0 with 100% discount, got {documento.neto_servicios}"

        # Verify total is not negative
        assert documento.total >= Decimal("0"), "Total should not be negative"


@pytest.mark.django_db
def test_descuento_0_porciento_repuestos():
    """Test 0% discount on repuestos - should have no discount effect"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaRepuesto
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_descuento_rep_0", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Descuento Rep 0", pais="CL")
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
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Test with 0% discount on repuestos
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_repuesto": [
            {
                "nombre": "Repuesto 0% discount",
                "cantidad": 3,
                "precio_unitario": "500.00",
                "descuento": "0.00",
                "codigo": "REP-001",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])
        linea = LineaRepuesto.objects.filter(documento=documento).first()

        # Verify discount is 0%
        assert linea.descuento == Decimal("0.00"), f"Discount should be 0%, got {linea.descuento}"

        # Verify totals are calculated correctly (no discount effect)
        expected_subtotal = Decimal("1500.00")  # 3 * 500.00
        assert (
            documento.neto_repuestos == expected_subtotal
        ), f"Neto repuestos should be {expected_subtotal}, got {documento.neto_repuestos}"
        assert (
            documento.total >= expected_subtotal
        ), f"Total should be at least {expected_subtotal}, got {documento.total}"
        assert documento.total >= Decimal("0"), "Total should not be negative"


@pytest.mark.django_db
def test_descuento_100_porciento_repuestos():
    """Test 100% discount on repuestos - should result in 0 neto"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaRepuesto
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_descuento_rep_100", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Descuento Rep 100", pais="CL")
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
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Test with 100% discount on repuestos
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_repuesto": [
            {
                "nombre": "Repuesto 100% discount",
                "cantidad": 1,
                "precio_unitario": "800.00",
                "descuento": "100.00",
                "codigo": "REP-002",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])
        linea = LineaRepuesto.objects.filter(documento=documento).first()

        # Verify discount is 100%
        assert linea.descuento == Decimal(
            "100.00"
        ), f"Discount should be 100%, got {linea.descuento}"

        # Verify neto repuestos is 0 (100% discount)
        assert documento.neto_repuestos == Decimal(
            "0.00"
        ), f"Neto repuestos should be 0 with 100% discount, got {documento.neto_repuestos}"

        # Verify total is not negative
        assert documento.total >= Decimal("0"), "Total should not be negative"


@pytest.mark.django_db
def test_descuentos_mixtos_servicios_repuestos():
    """Test mixed discount scenarios with both servicios and repuestos"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaRepuesto, LineaServicio
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_descuentos_mixtos", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Descuentos Mixtos", pais="CL")
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
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Mixed scenario: 0% discount on servicios, 100% discount on repuestos
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_servicio": [
            {
                "nombre": "Service 0% discount",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
            }
        ],
        "lineas_repuesto": [
            {
                "nombre": "Repuesto 100% discount",
                "cantidad": 1,
                "precio_unitario": "500.00",
                "descuento": "100.00",
                "codigo": "REP-003",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])

        linea_servicio = LineaServicio.objects.filter(documento=documento).first()
        linea_repuesto = LineaRepuesto.objects.filter(documento=documento).first()

        # Verify servicio discount is 0%
        assert linea_servicio.descuento == Decimal(
            "0.00"
        ), f"Servicio discount should be 0%, got {linea_servicio.descuento}"

        # Verify repuesto discount is 100%
        assert linea_repuesto.descuento == Decimal(
            "100.00"
        ), f"Repuesto discount should be 100%, got {linea_repuesto.descuento}"

        # Verify neto servicios is full amount (no discount)
        assert documento.neto_servicios == Decimal(
            "1000.00"
        ), f"Neto servicios should be 1000.00, got {documento.neto_servicios}"

        # Verify neto repuestos is 0 (100% discount)
        assert documento.neto_repuestos == Decimal(
            "0.00"
        ), f"Neto repuestos should be 0, got {documento.neto_repuestos}"

        # Verify total is not negative and includes servicios
        assert documento.total >= Decimal(
            "1000.00"
        ), f"Total should be at least 1000.00, got {documento.total}"
        assert documento.total >= Decimal("0"), "Total should not be negative"


@pytest.mark.django_db
def test_descuento_50_porciento_verificacion_calculos():
    """Test 50% discount to verify calculation logic"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_descuento_50", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Descuento 50", pais="CL")
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
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Test with 50% discount
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "lineas_servicio": [
            {
                "nombre": "Service 50% discount",
                "cantidad": 2,
                "precio_unitario": "1000.00",
                "descuento": "50.00",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])
        linea = LineaServicio.objects.filter(documento=documento).first()

        # Verify discount is 50%
        assert linea.descuento == Decimal("50.00"), f"Discount should be 50%, got {linea.descuento}"

        # Verify neto servicios is 50% of original (2 * 1000 * 0.5 = 1000)
        expected_neto = Decimal("1000.00")
        assert (
            documento.neto_servicios == expected_neto
        ), f"Neto servicios should be {expected_neto}, got {documento.neto_servicios}"

        # Verify total is not negative
        assert documento.total >= Decimal("0"), "Total should not be negative"
