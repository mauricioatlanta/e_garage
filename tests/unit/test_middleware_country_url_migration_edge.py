import pytest

from django.contrib.auth import get_user_model
from django.test import RequestFactory


@pytest.mark.django_db
def test_country_url_migration_edge_cases():
    """Test CountryUrlMigrationMiddleware with edge cases: ?next=, slash/no-slash, case variations"""
    try:
        from taller.middleware.country_url_migration import (
            CountryUrlMigrationMiddleware,
        )
    except ImportError:
        pytest.skip("CountryUrlMigrationMiddleware not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_migration", password="test")

    # Create empresa for the user
    from taller.models.empresa import Empresa

    empresa = Empresa.objects.create(user=user, nombre_taller="Test Migration", pais="CL")

    middleware = CountryUrlMigrationMiddleware(lambda r: None)
    factory = RequestFactory()

    # Test cases with various URL patterns
    test_cases = [
        # (path, expected_redirect, description)
        ("/us/vehiculos/", "/cl/vehiculos/", "US to CL redirect"),
        ("/us/vehiculos", "/cl/vehiculos/", "US to CL redirect (no trailing slash)"),
        (
            "/us/vehiculos/?next=/cl/documentos/",
            "/cl/vehiculos/?next=/cl/documentos/",
            "With next parameter",
        ),
        (
            "/us/vehiculos?next=/cl/documentos/",
            "/cl/vehiculos/?next=/cl/documentos/",
            "With next parameter (no trailing slash)",
        ),
        (
            "/us/vehiculos/?search=test&page=2",
            "/cl/vehiculos/?search=test&page=2",
            "With multiple query params",
        ),
        ("/Us/vehiculos/", "/cl/vehiculos/", "Case variation: Us to CL"),
        ("/US/vehiculos/", "/cl/vehiculos/", "Case variation: US to CL"),
        ("/cl/vehiculos/", None, "Already correct country (no redirect)"),
        ("/cl/vehiculos", "/cl/vehiculos/", "Add trailing slash"),
    ]

    for path, expected_redirect, description in test_cases:
        request = factory.get(path)
        request.user = user
        request.empresa = empresa

        response = middleware(request)

        if expected_redirect is None:
            # Should not redirect
            assert response is None, f"Failed for {description}: should not redirect"
        else:
            # Should redirect
            assert response is not None, f"Failed for {description}: should redirect"
            assert response.status_code == 302, f"Failed for {description}: should be 302 redirect"
            assert (
                response.url == expected_redirect
            ), f"Failed for {description}: expected {expected_redirect}, got {response.url}"


@pytest.mark.django_db
def test_country_url_migration_preserves_querystring():
    """Test that CountryUrlMigrationMiddleware preserves complex querystrings"""
    try:
        from taller.middleware.country_url_migration import (
            CountryUrlMigrationMiddleware,
        )
    except ImportError:
        pytest.skip("CountryUrlMigrationMiddleware not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_qs", password="test")

    from taller.models.empresa import Empresa

    empresa = Empresa.objects.create(user=user, nombre_taller="Test QS", pais="CL")

    middleware = CountryUrlMigrationMiddleware(lambda r: None)
    factory = RequestFactory()

    # Complex querystring cases
    complex_cases = [
        "/us/vehiculos/?search=test%20vehicle&page=2&sort=name&filter=active",
        "/us/vehiculos/?next=/cl/documentos/create/&from=search",
        "/us/vehiculos/?id=123&action=edit&tab=details",
    ]

    for path in complex_cases:
        request = factory.get(path)
        request.user = user
        request.empresa = empresa

        response = middleware(request)

        assert response is not None, f"Should redirect for {path}"
        assert response.status_code == 302, f"Should be 302 redirect for {path}"

        # Extract querystring from redirect URL
        redirect_url = response.url
        if "?" in redirect_url:
            querystring = redirect_url.split("?", 1)[1]
            original_querystring = path.split("?", 1)[1] if "?" in path else ""

            # Querystring should be preserved (order might change, but content should be same)
            assert querystring, f"Querystring should be preserved in {redirect_url}"
            # Basic check: should contain key parameters
            if "search=" in original_querystring:
                assert (
                    "search=" in querystring
                ), f"Search parameter should be preserved in {redirect_url}"


@pytest.mark.django_db
def test_country_url_migration_no_500_errors():
    """Test that CountryUrlMigrationMiddleware never causes 500 errors"""
    try:
        from taller.middleware.country_url_migration import (
            CountryUrlMigrationMiddleware,
        )
    except ImportError:
        pytest.skip("CountryUrlMigrationMiddleware not found")

    User = get_user_model()
    user = User.objects.create_user(username="test_no_500", password="test")

    from taller.models.empresa import Empresa

    empresa = Empresa.objects.create(user=user, nombre_taller="Test No 500", pais="CL")

    middleware = CountryUrlMigrationMiddleware(lambda r: None)
    factory = RequestFactory()

    # Edge cases that should not cause 500 errors
    edge_cases = [
        "/us/",  # root with country
        "/us",  # root without trailing slash
        "/us/vehiculos/../../admin/",  # path traversal attempt
        "/us/vehiculos/?next=javascript:alert(1)",  # XSS attempt in next
        "/us/vehiculos/?next=//evil.com/",  # external redirect attempt
        "/us/vehiculos/?next=/cl/vehiculos/?next=/us/vehiculos/",  # nested next
        "/us/vehiculos/?%20=%20",  # weird querystring
        "/us/vehiculos/?next=",  # empty next
        "/us/vehiculos/?next=/",  # root next
    ]

    for path in edge_cases:
        try:
            request = factory.get(path)
            request.user = user
            request.empresa = empresa

            response = middleware(request)

            # Should not raise exception and should return valid response
            assert response is None or (
                hasattr(response, "status_code") and response.status_code < 500
            ), f"Should not cause 500 error for {path}, got {response}"

        except Exception as e:
            pytest.fail(f"Middleware should not raise exception for {path}: {e}")
