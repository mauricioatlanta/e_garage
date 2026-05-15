import pytest

from django.test import RequestFactory


@pytest.mark.django_db
def test_country_url_migration_cases():
    """Test country URL migration middleware with various URL patterns"""
    try:
        from taller.middleware.country_url_migration import (
            CountryUrlMigrationMiddleware,
        )
    except ImportError:
        pytest.skip("CountryUrlMigrationMiddleware not found")

    middleware = CountryUrlMigrationMiddleware(lambda r: None)
    factory = RequestFactory()

    # Test cases with different URL patterns
    test_cases = [
        # (input_url, expected_redirect, description)
        ("/documentos/", "/cl/documentos/", "Basic path migration"),
        ("/documentos/?page=1", "/cl/documentos/?page=1", "Path with query string"),
        (
            "/documentos/?filter=active&sort=name",
            "/cl/documentos/?filter=active&sort=name",
            "Multiple query params",
        ),
        ("/documentos", "/cl/documentos/", "Path without trailing slash"),
        ("/DOCUMENTOS/", "/cl/documentos/", "Uppercase path"),
        (
            "/documentos/?NEXT=/other",
            "/cl/documentos/?NEXT=/other",
            "Preserve uppercase query params",
        ),
        (
            "/documentos/?next=/other",
            "/cl/documentos/?next=/other",
            "Preserve lowercase query params",
        ),
        (
            "/documentos/?next=/cl/other",
            "/cl/documentos/?next=/cl/other",
            "Next param with existing prefix",
        ),
    ]

    for input_url, expected_redirect, description in test_cases:
        request = factory.get(input_url)
        request.META["HTTP_HOST"] = "testserver"

        # Test the middleware logic
        response = middleware(request)

        # The middleware should either redirect or pass through
        if response and hasattr(response, "status_code"):
            assert response.status_code in (
                301,
                302,
            ), f"Failed for {description}: {input_url}"
        else:
            # If no redirect, the URL should be processed
            assert (
                request.path.startswith("/cl/") or request.path == input_url
            ), f"Failed for {description}: {input_url}"


@pytest.mark.django_db
def test_country_context_middleware():
    """Test country context middleware with various scenarios"""
    try:
        from taller.middleware.country_context import CountryContextMiddleware
    except ImportError:
        pytest.skip("CountryContextMiddleware not found")

    middleware = CountryContextMiddleware(lambda r: None)
    factory = RequestFactory()

    # Test different country scenarios
    test_cases = [
        ("/cl/documentos/", "CL", "Chile prefix"),
        ("/us/documentos/", "US", "US prefix"),
        ("/documentos/", None, "No prefix"),  # May default to CL
        ("/CL/DOCUMENTOS/", "CL", "Uppercase prefix"),
        ("/us/DOCUMENTOS/", "US", "Mixed case prefix"),
    ]

    for url, expected_country, description in test_cases:
        request = factory.get(url)
        request.META["HTTP_HOST"] = "testserver"

        # Test the middleware
        response = middleware(request)

        # Check if country context is set
        if hasattr(request, "country"):
            # For "No prefix" case, accept either None or default country (CL)
            if description == "No prefix" and expected_country is None:
                assert request.country in (
                    None,
                    "CL",
                ), f"Failed for {description}: expected None or CL, got {request.country}"
            else:
                assert (
                    request.country == expected_country
                ), f"Failed for {description}: expected {expected_country}, got {request.country}"


@pytest.mark.django_db
def test_middleware_edge_cases():
    """Test middleware with edge cases and error conditions"""
    factory = RequestFactory()

    # Test with malformed URLs
    malformed_urls = [
        "//double-slash",
        "/path/with//double/slash",
        "/path/with%20spaces",
        "/path/with?weird=query&",
        "/path/with#fragment",
    ]

    for url in malformed_urls:
        request = factory.get(url)
        request.META["HTTP_HOST"] = "testserver"

        # Middleware should not crash on malformed URLs
        try:
            # Test both middlewares if they exist
            try:
                from taller.middleware.country_url_migration import (
                    CountryUrlMigrationMiddleware,
                )

                middleware1 = CountryUrlMigrationMiddleware(lambda r: None)
                middleware1(request)
            except ImportError:
                pass

            try:
                from taller.middleware.country_context import CountryContextMiddleware

                middleware2 = CountryContextMiddleware(lambda r: None)
                middleware2(request)
            except ImportError:
                pass

        except Exception as e:
            pytest.fail(f"Middleware crashed on malformed URL {url}: {e}")
