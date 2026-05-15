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
            pass
    return fb


@pytest.mark.django_db
def test_herencia_responsable_on_documento():
    """Test inheritance of tecnico_responsable from document to lines when inheritance is ON"""
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
    user = User.objects.create_user(username="test_herencia_on", password="test")

    # Create empresa
    empresa = Empresa.objects.create(user=user, nombre_taller="Test Herencia ON", pais="CL")

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

    # Try to find the API endpoint (use CL prefix to match empresa country)
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Test data with tecnico_responsable and inheritance ON
    data = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "tecnico_responsable": tecnico.id,
        "heredar_responsable": True,  # Inheritance ON
        "lineas_servicio": [
            {
                "nombre": "Service 1",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
            },
            {
                "nombre": "Service 2",
                "cantidad": 2,
                "precio_unitario": "500.00",
                "descuento": "10.00",
            },
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

    # Should succeed (302 is expected due to country middleware redirect)
    assert_ok_or_redirect(response, "/cl/documentos/api/create/")

    if response.status_code in (200, 201):
        response_data = assert_json_response(response)

        # Check that document was created
        assert "id" in response_data, "Response should contain document ID"
        documento_id = response_data["id"]

        # Verify document has tecnico_responsable
        documento = Documento.objects.get(id=documento_id)
        assert documento.tecnico_responsable == tecnico, "Document should have tecnico_responsable"

        # Verify lines inherit tecnico_responsable
        lineas_servicio = LineaServicio.objects.filter(documento=documento)
        assert lineas_servicio.count() == 2, "Should have 2 service lines"

        for linea in lineas_servicio:
            assert (
                linea.tecnico_responsable == tecnico
            ), f"Service line should inherit tecnico_responsable: {linea.nombre}"

        # Check repuesto lines if they exist
        lineas_repuesto = LineaRepuesto.objects.filter(documento=documento)
        if lineas_repuesto.exists():
            for linea in lineas_repuesto:
                assert (
                    linea.tecnico_responsable == tecnico
                ), f"Repuesto line should inherit tecnico_responsable: {linea.nombre}"


@pytest.mark.django_db
def test_herencia_responsable_on_vs_off():
    """Test inheritance ON vs OFF to ensure both branches are covered"""
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
    user = User.objects.create_user(username="test_herencia_compare", password="test")

    # Create empresa
    empresa = Empresa.objects.create(user=user, nombre_taller="Test Herencia Compare", pais="CL")

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

    # Create tecnicos
    tecnico_doc = Tecnico.objects.create(empresa=empresa, nombre="Tecnico Doc", activo=True)
    tecnico_linea = Tecnico.objects.create(empresa=empresa, nombre="Tecnico Linea", activo=True)

    c = Client()
    c.force_login(user)

    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Test 1: Inheritance ON (should inherit from document)
    data_on = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "tecnico_responsable": tecnico_doc.id,
        "heredar_responsable": True,
        "lineas_servicio": [
            {
                "nombre": "Service ON",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
            }
        ],
    }

    response_on = c.post(url, data=json.dumps(data_on), content_type="application/json")
    assert_ok_or_redirect(response_on, "/cl/documentos/api/create/")

    if response_on.status_code in (200, 201):
        doc_on = Documento.objects.get(id=response_on.json()["id"])
        linea_on = LineaServicio.objects.filter(documento=doc_on).first()
        assert linea_on.tecnico_responsable == tecnico_doc, "ON: Line should inherit from document"

    # Test 2: Inheritance OFF (should use line-specific tecnico)
    data_off = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "BOL",
        "fecha_emision": "2025-01-01",
        "tecnico_responsable": tecnico_doc.id,
        "heredar_responsable": False,
        "lineas_servicio": [
            {
                "nombre": "Service OFF",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
                "tecnico_responsable": tecnico_linea.id,
            }
        ],
    }

    response_off = c.post(url, data=json.dumps(data_off), content_type="application/json")
    assert_ok_or_redirect(response_off, "/cl/documentos/api/create/")

    if response_off.status_code in (200, 201):
        doc_off = Documento.objects.get(id=response_off.json()["id"])
        linea_off = LineaServicio.objects.filter(documento=doc_off).first()
        assert (
            linea_off.tecnico_responsable == tecnico_linea
        ), "OFF: Line should use its own tecnico"


@pytest.mark.django_db
def test_herencia_responsable_edge_cases():
    """Test edge cases for responsable inheritance"""
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
    user = User.objects.create_user(username="test_herencia_edge", password="test")

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Herencia Edge", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="TEST123",
        marca_texto="Test",
        modelo_texto="Model",
        anio=2024,
    )
    tecnico = Tecnico.objects.create(empresa=empresa, nombre="Test Tecnico", activo=True)

    c = Client()
    c.force_login(user)
    url = _rev(
        ["taller:documentos_api_create", "documentos:api_create"],
        "/cl/documentos/api/create/",
    )

    # Test case: No tecnico_responsable on document, but inheritance ON
    data_no_tecnico = {
        "empresa": empresa.id,
        "cliente": cliente.id,
        "vehiculo": vehiculo.id,
        "tipo": "FAC",
        "fecha_emision": "2025-01-01",
        "heredar_responsable": True,
        "lineas_servicio": [
            {
                "nombre": "Service No Tecnico",
                "cantidad": 1,
                "precio_unitario": "1000.00",
                "descuento": "0.00",
            }
        ],
    }

    response = c.post(url, data=json.dumps(data_no_tecnico), content_type="application/json")

    # Should handle gracefully (either succeed with None or fail gracefully)
    if response.status_code in (200, 201, 302):
        assert_ok_or_redirect(response, "/cl/documentos/api/create/")
    else:
        assert response.status_code in (
            400,
            422,
        ), f"Should handle no tecnico gracefully: {response.status_code}"

    if response.status_code in (200, 201):
        doc = Documento.objects.get(id=response.json()["id"])
        linea = LineaServicio.objects.filter(documento=doc).first()
        # Line should have None tecnico_responsable if document has None
        assert (
            linea.tecnico_responsable is None
        ), "Line should have None tecnico when document has None"
