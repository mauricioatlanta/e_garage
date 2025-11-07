"""
Test that country middleware redirects preserve querystring parameters.

This ensures that when users are redirected from /us/ to /cl/ URLs,
important parameters like ?next= are preserved.
"""

import pytest
import json
from django.test import Client
from django.contrib.auth import get_user_model
from tests.test_utils.http_asserts import assert_redirect_preserves_querystring


@pytest.mark.django_db
def test_redirect_preserves_querystring_get():
    """Test that GET redirects preserve querystring parameters"""
    User = get_user_model()
    user = User.objects.create_user(username="test_redirect_qs", password="test")

    c = Client()
    c.force_login(user)

    # Test GET request with querystring that should be preserved
    response = c.get("/us/documentos/api/create/?next=/us/vehiculos/&param=value")
    
    # Should redirect and preserve querystring
    assert_redirect_preserves_querystring(
        response, 
        expected_base_path="/cl/documentos/api/create/",
        expected_params={"next": "/us/vehiculos/", "param": "value"}
    )


@pytest.mark.django_db
def test_redirect_preserves_querystring_post():
    """Test that POST redirects preserve querystring parameters"""
    User = get_user_model()
    user = User.objects.create_user(username="test_redirect_qs_post", password="test")

    c = Client()
    c.force_login(user)

    # Test POST request with querystring that should be preserved
    data = {"test": "data"}
    response = c.post("/us/documentos/api/create/?next=/us/vehiculos/&param=value", 
                     data=json.dumps(data), content_type="application/json")
    
    # Should redirect and preserve querystring
    assert_redirect_preserves_querystring(
        response, 
        expected_base_path="/cl/documentos/api/create/",
        expected_params={"next": "/us/vehiculos/", "param": "value"}
    )


@pytest.mark.django_db
def test_redirect_preserves_complex_querystring():
    """Test that complex querystrings are preserved correctly"""
    User = get_user_model()
    user = User.objects.create_user(username="test_redirect_complex", password="test")

    c = Client()
    c.force_login(user)

    # Test with complex querystring including special characters
    complex_qs = "/us/documentos/api/create/?next=/us/vehiculos/&search=test%20query&page=2&filter=active"
    response = c.get(complex_qs)
    
    # Should redirect and preserve all parameters
    assert_redirect_preserves_querystring(
        response, 
        expected_base_path="/cl/documentos/api/create/",
        expected_params={
            "next": "/us/vehiculos/", 
            "search": "test query",  # URL decoded
            "page": "2", 
            "filter": "active"
        }
    )


@pytest.mark.django_db
def test_redirect_without_querystring():
    """Test that redirects without querystring work normally"""
    User = get_user_model()
    user = User.objects.create_user(username="test_redirect_no_qs", password="test")

    c = Client()
    c.force_login(user)

    # Test simple redirect without querystring
    response = c.get("/us/documentos/api/create/")
    
    # Should redirect to clean URL
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert location == "/cl/documentos/api/create/", f"Expected clean redirect, got {location}"


@pytest.mark.django_db
def test_redirect_preserves_querystring_different_endpoints():
    """Test querystring preservation across different endpoints"""
    User = get_user_model()
    user = User.objects.create_user(username="test_redirect_endpoints", password="test")

    c = Client()
    c.force_login(user)

    # Test different endpoints that should all preserve querystring
    endpoints = [
        "/us/vehiculos/api/create/",
        "/us/clientes/api/create/",
        "/us/repuestos/api/create/",
    ]
    
    for endpoint in endpoints:
        expected_cl_endpoint = endpoint.replace("/us/", "/cl/")
        response = c.get(f"{endpoint}?next=/us/dashboard/&param=test")
        
        assert_redirect_preserves_querystring(
            response,
            expected_base_path=expected_cl_endpoint,
            expected_params={"next": "/us/dashboard/", "param": "test"}
        )
