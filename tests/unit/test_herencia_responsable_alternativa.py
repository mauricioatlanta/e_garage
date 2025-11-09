"""
Test alternative inheritance scenarios for tecnico_responsable.

These tests cover edge cases and alternative branches in the inheritance logic:
- Document with tecnico, line without tecnico (should inherit)
- Document with tecnico, line with different tecnico (should not override)
- Document without tecnico, line with tecnico (should use line's tecnico)
- Mixed scenarios with multiple lines
"""

import json

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
def test_herencia_documento_con_tecnico_linea_sin_tecnico():
    """Test: Document has tecnico, line has no tecnico -> line should inherit"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.tecnico import Tecnico
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_herencia_alt1", password="test")

    empresa = Empresa.objects.create(
        user=user, nombre_taller="Test Herencia Alt1", pais="CL"
    )
    cliente = Cliente.objects.create(
        empresa=empresa, nombre="Test Client", tax_id="1-9"
    )
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca_texto="Test",
        modelo_texto="Model",
        anio=2024,
    )
    tecnico_doc = Tecnico.objects.create(
        empresa=empresa, nombre="Tecnico Doc", activo=True
    )

    c = Client()
    c.force_login(user)
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Document has tecnico, line has no tecnico (should inherit)
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "tecnico_responsable": tecnico_doc.id,
        "heredar_responsable": True,
        "lineas_servicio": [
            {
                "nombre": "Service without tecnico",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
                # No tecnico_responsable specified
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])
        linea = LineaServicio.objects.filter(documento=documento).first()

        # Document should have tecnico
        assert (
            documento.tecnico_responsable == tecnico_doc
        ), "Document should have tecnico_responsable"

        # Line should inherit from document
        assert (
            linea.tecnico_responsable == tecnico_doc
        ), "Line should inherit tecnico_responsable from document"


@pytest.mark.django_db
def test_herencia_documento_con_tecnico_linea_con_tecnico_diferente():
    """Test: Document has tecnico, line has different tecnico -> line should keep its own"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.tecnico import Tecnico
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_herencia_alt2", password="test")

    empresa = Empresa.objects.create(
        user=user, nombre_taller="Test Herencia Alt2", pais="CL"
    )
    cliente = Cliente.objects.create(
        empresa=empresa, nombre="Test Client", tax_id="1-9"
    )
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca_texto="Test",
        modelo_texto="Model",
        anio=2024,
    )
    tecnico_doc = Tecnico.objects.create(
        empresa=empresa, nombre="Tecnico Doc", activo=True
    )
    tecnico_linea = Tecnico.objects.create(
        empresa=empresa, nombre="Tecnico Linea", activo=True
    )

    c = Client()
    c.force_login(user)
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Document has tecnico, line has different tecnico (should not override)
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "tecnico_responsable": tecnico_doc.id,
        "heredar_responsable": True,  # Inheritance is ON
        "lineas_servicio": [
            {
                "nombre": "Service with different tecnico",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
                "tecnico_responsable": tecnico_linea.id,  # Different tecnico
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])
        linea = LineaServicio.objects.filter(documento=documento).first()

        # Document should have its tecnico
        assert (
            documento.tecnico_responsable == tecnico_doc
        ), "Document should have its tecnico_responsable"

        # Line should keep its own tecnico (not inherit from document)
        assert (
            linea.tecnico_responsable == tecnico_linea
        ), "Line should keep its own tecnico_responsable"


@pytest.mark.django_db
def test_herencia_documento_sin_tecnico_linea_con_tecnico():
    """Test: Document has no tecnico, line has tecnico -> line should use its own"""
    try:
        from taller.models.clientes import Cliente
        from taller.models.documento import Documento
        from taller.models.empresa import Empresa
        from taller.models.lineas_documento import LineaServicio
        from taller.models.tecnico import Tecnico
        from taller.models.vehiculos import Vehiculo
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_herencia_alt3", password="test")

    empresa = Empresa.objects.create(
        user=user, nombre_taller="Test Herencia Alt3", pais="CL"
    )
    cliente = Cliente.objects.create(
        empresa=empresa, nombre="Test Client", tax_id="1-9"
    )
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca_texto="Test",
        modelo_texto="Model",
        anio=2024,
    )
    tecnico_linea = Tecnico.objects.create(
        empresa=empresa, nombre="Tecnico Linea", activo=True
    )

    c = Client()
    c.force_login(user)
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Document has no tecnico, line has tecnico
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        # No tecnico_responsable on document
        "heredar_responsable": True,
        "lineas_servicio": [
            {
                "nombre": "Service with tecnico",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
                "tecnico_responsable": tecnico_linea.id,
            }
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])
        linea = LineaServicio.objects.filter(documento=documento).first()

        # Document should have no tecnico
        assert (
            documento.tecnico_responsable is None
        ), "Document should have no tecnico_responsable"

        # Line should have its own tecnico
        assert (
            linea.tecnico_responsable == tecnico_linea
        ), "Line should have its own tecnico_responsable"


@pytest.mark.django_db
def test_herencia_mixta_multiple_lineas():
    """Test: Mixed scenario with multiple lines - some inherit, some don't"""
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
    user = User.objects.create_user(username="test_herencia_mixta", password="test")

    empresa = Empresa.objects.create(
        user=user, nombre_taller="Test Herencia Mixta", pais="CL"
    )
    cliente = Cliente.objects.create(
        empresa=empresa, nombre="Test Client", tax_id="1-9"
    )
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca_texto="Test",
        modelo_texto="Model",
        anio=2024,
    )
    tecnico_doc = Tecnico.objects.create(
        empresa=empresa, nombre="Tecnico Doc", activo=True
    )
    tecnico_linea1 = Tecnico.objects.create(
        empresa=empresa, nombre="Tecnico Linea1", activo=True
    )
    tecnico_linea2 = Tecnico.objects.create(
        empresa=empresa, nombre="Tecnico Linea2", activo=True
    )

    c = Client()
    c.force_login(user)
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Mixed scenario: document has tecnico, lines have different behaviors
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "tecnico_responsable": tecnico_doc.id,
        "heredar_responsable": True,
        "lineas_servicio": [
            {
                "nombre": "Service inherits from doc",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
                # No tecnico_responsable - should inherit
            },
            {
                "nombre": "Service has own tecnico",
                "cantidad": 1,
                "precio_unitario": "2000.00",
                "descuento": "0.00",
                "tecnico_responsable": tecnico_linea1.id,
            },
        ],
        "lineas_repuesto": [
            {
                "nombre": "Repuesto inherits from doc",
                "cantidad": 1,
                "precio_unitario": "500.00",
                "descuento": "0.00",
                "codigo": "REP-001",
                # No tecnico_responsable - should inherit
            },
            {
                "nombre": "Repuesto has own tecnico",
                "cantidad": 1,
                "precio_unitario": "750.00",
                "descuento": "0.00",
                "codigo": "REP-002",
                "tecnico_responsable": tecnico_linea2.id,
            },
        ],
    }

    response = c.post(url, data=json.dumps(data), content_type="application/json")
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)
        documento = Documento.objects.get(id=response_data["id"])

        # Document should have its tecnico
        assert (
            documento.tecnico_responsable == tecnico_doc
        ), "Document should have its tecnico_responsable"

        # Get all lines
        lineas_servicio = LineaServicio.objects.filter(documento=documento).order_by(
            "id"
        )
        lineas_repuesto = LineaRepuesto.objects.filter(documento=documento).order_by(
            "id"
        )

        # First service line should inherit from document
        assert (
            lineas_servicio[0].tecnico_responsable == tecnico_doc
        ), "First service line should inherit from document"

        # Second service line should have its own tecnico
        assert (
            lineas_servicio[1].tecnico_responsable == tecnico_linea1
        ), "Second service line should have its own tecnico"

        # First repuesto line should inherit from document
        assert (
            lineas_repuesto[0].tecnico_responsable == tecnico_doc
        ), "First repuesto line should inherit from document"

        # Second repuesto line should have its own tecnico
        assert (
            lineas_repuesto[1].tecnico_responsable == tecnico_linea2
        ), "Second repuesto line should have its own tecnico"
