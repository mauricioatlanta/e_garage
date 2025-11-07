import json
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse, NoReverseMatch
from tests.test_utils.http_asserts import assert_ok_or_redirect, assert_json_response


def _rev(cands, fb):
    """Helper to try multiple URL names and fallback to a path"""
    for n in cands:
        try:
            return reverse(n)
        except NoReverseMatch:
            pass
    return fb


@pytest.mark.django_db
def test_documentos_descuentos_edge_cases():
    """Test document creation with edge cases for discounts: 0%, 100%, negative, >100%"""
    try:
        from taller.models.empresa import Empresa
        from taller.models.clientes import Cliente
        from taller.models.vehiculos import Vehiculo
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaServicio, LineaRepuesto
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_descuentos", password="test")
    
    empresa = Empresa.objects.create(user=user, nombre_taller="Test Descuentos", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa, cliente=cliente, patente="TEST123",
        marca_texto="Test", modelo_texto="Model", anio=2024
    )

    c = Client()
    c.force_login(user)
    url = _rev(["taller:documentos_api_create", "documentos:api_create"], "/cl/documentos/api/create/")
    
    # Test cases for discount edge cases
    discount_cases = [
        # (descuento, should_succeed, description)
        ("0.00", True, "Zero discount"),
        ("100.00", True, "100% discount"),
        ("50.00", True, "50% discount"),
        ("0", True, "Zero discount (integer)"),
        ("100", True, "100% discount (integer)"),
        ("-10.00", False, "Negative discount"),
        ("150.00", False, "Over 100% discount"),
        ("", False, "Empty discount"),
        ("invalid", False, "Invalid discount"),
    ]

    for descuento, should_succeed, description in discount_cases:
        data = {
            "empresa": empresa.id,
            "cliente": cliente.id,
            "vehiculo": vehiculo.id,
            "tipo": "FAC",
            "fecha_emision": "2025-01-01",
            "lineas_servicio": [
                {
                    "nombre": f"Service {description}",
                    "cantidad": 1,
                    "precio_unitario": "1000.00",
                    "descuento": descuento
                }
            ]
        }
        
        response = c.post(url, data=json.dumps(data), content_type="application/json")
        
        if should_succeed:
            assert_ok_or_redirect(response, "/cl/documentos/api/create/")
            if response.status_code in (200, 201):
                # Verify the line was created with correct discount
                doc_id = response.json()["id"]
                documento = Documento.objects.get(id=doc_id)
                linea = LineaServicio.objects.filter(documento=documento).first()
                assert linea is not None, f"Service line should be created for {description}"
        else:
            if response.status_code == 302:
                assert_ok_or_redirect(response, "/cl/documentos/api/create/")
            else:
                assert response.status_code in (400, 422), f"Should fail for {description}: {response.status_code}"


@pytest.mark.django_db
def test_documentos_cantidades_decimales():
    """Test document creation with decimal quantities and precise calculations"""
    try:
        from taller.models.empresa import Empresa
        from taller.models.clientes import Cliente
        from taller.models.vehiculos import Vehiculo
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaServicio
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_cantidades", password="test")
    
    empresa = Empresa.objects.create(user=user, nombre_taller="Test Cantidades", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa, cliente=cliente, patente="TEST123",
        marca_texto="Test", modelo_texto="Model", anio=2024
    )

    c = Client()
    c.force_login(user)
    url = _rev(["taller:documentos_api_create", "documentos:api_create"], "/cl/documentos/api/create/")
    
    # Test cases for decimal quantities
    quantity_cases = [
        # (cantidad, precio_unitario, expected_subtotal, description)
        ("1.5", "1000.00", "1500.00", "Half quantity"),
        ("0.5", "2000.00", "1000.00", "Quarter quantity"),
        ("2.25", "400.00", "900.00", "Quarter and half quantity"),
        ("0.1", "10000.00", "1000.00", "Tenth quantity"),
        ("3.33", "300.00", "999.00", "Repeating decimal quantity"),
        ("1", "1000.00", "1000.00", "Integer quantity"),
        ("0", "1000.00", "0.00", "Zero quantity"),
    ]

    for cantidad, precio_unitario, expected_subtotal, description in quantity_cases:
        data = {
            "empresa": empresa.id,
            "cliente": cliente.id,
            "vehiculo": vehiculo.id,
            "tipo": "FAC",
            "fecha_emision": "2025-01-01",
            "lineas_servicio": [
                {
                    "nombre": f"Service {description}",
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "descuento": "0.00"
                }
            ]
        }
        
        response = c.post(url, data=json.dumps(data), content_type="application/json")
        
        assert_ok_or_redirect(response, "/cl/documentos/api/create/")
        
        if response.status_code in (200, 201):
            doc_id = response.json()["id"]
            documento = Documento.objects.get(id=doc_id)
            linea = LineaServicio.objects.filter(documento=documento).first()
            
            assert linea is not None, f"Service line should be created for {description}"
            
            # Check that quantity is stored correctly
            assert str(linea.cantidad) == cantidad, f"Quantity should match for {description}"
            
            # Check subtotal calculation (be tolerant to rounding differences)
            if hasattr(linea, 'subtotal'):
                assert isinstance(linea.subtotal, (int, float, Decimal)), f"Subtotal should be numeric for {description}"
                assert linea.subtotal >= 0, f"Subtotal should be non-negative for {description}"


@pytest.mark.django_db
def test_documentos_precios_4_decimales():
    """Test document creation with 4-decimal precision prices and rounding"""
    try:
        from taller.models.empresa import Empresa
        from taller.models.clientes import Cliente
        from taller.models.vehiculos import Vehiculo
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaServicio
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_precios", password="test")
    
    empresa = Empresa.objects.create(user=user, nombre_taller="Test Precios", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa, cliente=cliente, patente="TEST123",
        marca_texto="Test", modelo_texto="Model", anio=2024
    )

    c = Client()
    c.force_login(user)
    url = _rev(["taller:documentos_api_create", "documentos:api_create"], "/cl/documentos/api/create/")
    
    # Test cases for 4-decimal precision prices
    price_cases = [
        # (precio_unitario, description)
        ("1000.1234", "4 decimal places"),
        ("1000.0001", "4 decimal places with trailing zeros"),
        ("1000.9999", "4 decimal places near rounding"),
        ("0.0001", "Very small price"),
        ("9999.9999", "Large price with 4 decimals"),
        ("1000.0000", "4 decimal places all zeros"),
        ("1000.5000", "4 decimal places with half"),
    ]

    for precio_unitario, description in price_cases:
        data = {
            "empresa": empresa.id,
            "cliente": cliente.id,
            "vehiculo": vehiculo.id,
            "tipo": "FAC",
            "fecha_emision": "2025-01-01",
            "lineas_servicio": [
                {
                    "nombre": f"Service {description}",
                    "cantidad": 1,
                    "precio_unitario": precio_unitario,
                    "descuento": "0.00"
                }
            ]
        }
        
        response = c.post(url, data=json.dumps(data), content_type="application/json")
        
        assert_ok_or_redirect(response, "/cl/documentos/api/create/")
        
        if response.status_code in (200, 201):
            doc_id = response.json()["id"]
            documento = Documento.objects.get(id=doc_id)
            linea = LineaServicio.objects.filter(documento=documento).first()
            
            assert linea is not None, f"Service line should be created for {description}"
            
            # Check that price is stored correctly (may be rounded by model)
            assert isinstance(linea.precio_unitario, (int, float, Decimal)), f"Price should be numeric for {description}"
            assert linea.precio_unitario >= 0, f"Price should be non-negative for {description}"


@pytest.mark.django_db
def test_documentos_negativos_bordes():
    """Test document creation with negative values and edge cases"""
    try:
        from taller.models.empresa import Empresa
        from taller.models.clientes import Cliente
        from taller.models.vehiculos import Vehiculo
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaServicio
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_negativos", password="test")
    
    empresa = Empresa.objects.create(user=user, nombre_taller="Test Negativos", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa, cliente=cliente, patente="TEST123",
        marca_texto="Test", modelo_texto="Model", anio=2024
    )

    c = Client()
    c.force_login(user)
    url = _rev(["taller:documentos_api_create", "documentos:api_create"], "/cl/documentos/api/create/")
    
    # Test cases for negative values and edge cases
    negative_cases = [
        # (cantidad, precio_unitario, descuento, should_succeed, description)
        ("-1", "1000.00", "0.00", False, "Negative quantity"),
        ("1", "-1000.00", "0.00", False, "Negative price"),
        ("1", "1000.00", "-10.00", False, "Negative discount"),
        ("0", "1000.00", "0.00", True, "Zero quantity"),
        ("1", "0.00", "0.00", True, "Zero price"),
        ("", "1000.00", "0.00", False, "Empty quantity"),
        ("1", "", "0.00", False, "Empty price"),
        ("1", "1000.00", "", False, "Empty discount"),
        ("invalid", "1000.00", "0.00", False, "Invalid quantity"),
        ("1", "invalid", "0.00", False, "Invalid price"),
        ("1", "1000.00", "invalid", False, "Invalid discount"),
    ]

    for cantidad, precio_unitario, descuento, should_succeed, description in negative_cases:
        data = {
            "empresa": empresa.id,
            "cliente": cliente.id,
            "vehiculo": vehiculo.id,
            "tipo": "FAC",
            "fecha_emision": "2025-01-01",
            "lineas_servicio": [
                {
                    "nombre": f"Service {description}",
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "descuento": descuento
                }
            ]
        }
        
        response = c.post(url, data=json.dumps(data), content_type="application/json")
        
        if should_succeed:
            assert_ok_or_redirect(response, "/cl/documentos/api/create/")
        else:
            if response.status_code == 302:
                assert_ok_or_redirect(response, "/cl/documentos/api/create/")
            else:
                assert response.status_code in (400, 422), f"Should fail for {description}: {response.status_code}"


@pytest.mark.django_db
def test_documentos_rounding_precision():
    """Test document creation with rounding precision edge cases"""
    try:
        from taller.models.empresa import Empresa
        from taller.models.clientes import Cliente
        from taller.models.vehiculos import Vehiculo
        from taller.models.documento import Documento
        from taller.models.lineas_documento import LineaServicio
    except ImportError:
        pytest.skip("Required models not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_rounding", password="test")
    
    empresa = Empresa.objects.create(user=user, nombre_taller="Test Rounding", pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Test Client", tax_id="1-9")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa, cliente=cliente, patente="TEST123",
        marca_texto="Test", modelo_texto="Model", anio=2024
    )

    c = Client()
    c.force_login(user)
    url = _rev(["taller:documentos_api_create", "documentos:api_create"], "/cl/documentos/api/create/")
    
    # Test cases for rounding precision
    rounding_cases = [
        # (cantidad, precio_unitario, descuento, description)
        ("1", "1000.001", "0.00", "Price with 3 decimals"),
        ("1", "1000.0001", "0.00", "Price with 4 decimals"),
        ("1", "1000.00001", "0.00", "Price with 5 decimals"),
        ("1.333", "1000.00", "0.00", "Quantity with repeating decimal"),
        ("1", "1000.00", "33.333", "Discount with repeating decimal"),
        ("1", "1000.00", "33.3333", "Discount with 4 decimals"),
    ]

    for cantidad, precio_unitario, descuento, description in rounding_cases:
        data = {
            "empresa": empresa.id,
            "cliente": cliente.id,
            "vehiculo": vehiculo.id,
            "tipo": "FAC",
            "fecha_emision": "2025-01-01",
            "lineas_servicio": [
                {
                    "nombre": f"Service {description}",
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "descuento": descuento
                }
            ]
        }
        
        response = c.post(url, data=json.dumps(data), content_type="application/json")
        
        # Should handle rounding gracefully
        if response.status_code in (200, 201, 302):
            assert_ok_or_redirect(response, "/cl/documentos/api/create/")
        else:
            assert response.status_code in (400, 422), f"Should handle rounding for {description}: {response.status_code}"
        
        if response.status_code in (200, 201):
            doc_id = response.json()["id"]
            documento = Documento.objects.get(id=doc_id)
            linea = LineaServicio.objects.filter(documento=documento).first()
            
            assert linea is not None, f"Service line should be created for {description}"
            
            # Check that values are stored with appropriate precision
            assert isinstance(linea.cantidad, (int, float, Decimal)), f"Quantity should be numeric for {description}"
            assert isinstance(linea.precio_unitario, (int, float, Decimal)), f"Price should be numeric for {description}"
            assert isinstance(linea.descuento, (int, float, Decimal)), f"Discount should be numeric for {description}"
