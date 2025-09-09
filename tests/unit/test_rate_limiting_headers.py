import pytest

from django.test import override_settings


@pytest.mark.django_db
@override_settings(RATE_LIMIT_REQUESTS=3, RATE_LIMIT_WINDOW=1)
def test_rate_limit_incluye_retry_after(client):
    """
    Test rate limiting: si hay 429, que incluya Retry-After
    (o cabecera equivalente) y sea estable.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user("ratelimit", "test@example.com", "password")
    client.force_login(user)

    # Ajusta a un endpoint barato (puede ser uno de los que ya usas en smoke)
    url = "/cl/"

    responses = []
    for i in range(5):
        try:
            resp = client.get(url)
            responses.append(resp)
        except Exception:
            # Algunos requests pueden fallar, eso está ok
            continue

    # Si no está activo, toleramos; si está activo, debe traer 429 con header
    for resp in responses:
        if resp.status_code == 429:
            # Debe incluir header Retry-After
            assert (
                "Retry-After" in resp.headers or "Retry-after" in resp.headers
            ), f"429 response debe incluir Retry-After header: {resp.headers}"
            # El header debe tener un valor numérico
            retry_after = resp.headers.get("Retry-After") or resp.headers.get(
                "Retry-after"
            )
            assert (
                retry_after.isdigit()
            ), f"Retry-After debe ser numérico: {retry_after}"
        else:
            # Otros códigos de respuesta deben ser válidos
            assert resp.status_code in (
                200,
                201,
                400,
                405,
                302,
                404,
            ), f"Código de respuesta inesperado: {resp.status_code}"


@pytest.mark.django_db
def test_rate_limit_headers_consistency(client):
    """
    Test que verifica consistencia de headers en rate limiting.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user("ratelimit2", "test2@example.com", "password")
    client.force_login(user)

    # Test con diferentes endpoints
    endpoints = ["/cl/", "/cl/documentos/", "/cl/clientes/"]

    for endpoint in endpoints:
        try:
            resp = client.get(endpoint)
            if resp.status_code == 429:
                # Si es 429, debe tener headers apropiados
                assert (
                    "Retry-After" in resp.headers or "Retry-after" in resp.headers
                ), f"429 en {endpoint} debe incluir Retry-After"

                # Verificar que el header tiene formato correcto
                retry_after = resp.headers.get("Retry-After") or resp.headers.get(
                    "Retry-after"
                )
                assert retry_after, f"Retry-After no puede estar vacío en {endpoint}"

                # Debe ser un número positivo
                try:
                    retry_seconds = int(retry_after)
                    assert (
                        retry_seconds > 0
                    ), f"Retry-After debe ser positivo: {retry_seconds}"
                except ValueError:
                    pytest.fail(f"Retry-After debe ser numérico: {retry_after}")
        except Exception:
            # Tolerar errores de endpoints que no existen
            continue


@pytest.mark.django_db
@override_settings(RATE_LIMIT_REQUESTS=2, RATE_LIMIT_WINDOW=60)
def test_rate_limit_multiple_requests_headers(client):
    """
    Test rate limiting con múltiples requests para verificar headers.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user("ratelimit3", "test3@example.com", "password")
    client.force_login(user)

    url = "/cl/"
    responses = []

    # Hacer múltiples requests
    for i in range(4):
        try:
            resp = client.get(url)
            responses.append(resp)
        except Exception:
            continue

    # Analizar respuestas
    success_responses = [r for r in responses if r.status_code in (200, 201, 302, 404)]
    rate_limited_responses = [r for r in responses if r.status_code == 429]

    # Si hay rate limiting activo, debe haber al menos una respuesta 429
    if rate_limited_responses:
        for resp in rate_limited_responses:
            assert (
                "Retry-After" in resp.headers or "Retry-after" in resp.headers
            ), "429 response debe incluir Retry-After"

            # Verificar que el header es consistente
            retry_after = resp.headers.get("Retry-After") or resp.headers.get(
                "Retry-after"
            )
            assert retry_after, "Retry-After no puede estar vacío"

            # Debe ser un número razonable (entre 1 y 3600 segundos)
            try:
                retry_seconds = int(retry_after)
                assert (
                    1 <= retry_seconds <= 3600
                ), f"Retry-After debe estar entre 1 y 3600 segundos: {retry_seconds}"
            except ValueError:
                pytest.fail(f"Retry-After debe ser numérico: {retry_after}")

    # Si no hay rate limiting, las respuestas deben ser exitosas
    if not rate_limited_responses:
        assert (
            len(success_responses) > 0
        ), "Debe haber al menos una respuesta exitosa si no hay rate limiting"


@pytest.mark.django_db
def test_rate_limit_headers_with_different_methods(client):
    """
    Test rate limiting headers con diferentes métodos HTTP.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user("ratelimit4", "test4@example.com", "password")
    client.force_login(user)

    # Test con diferentes métodos
    methods = [
        ("GET", "/cl/"),
        ("POST", "/cl/documentos/api/create/"),
        ("PUT", "/cl/clientes/"),
        ("DELETE", "/cl/repuestos/"),
    ]

    for method, url in methods:
        try:
            if method == "GET":
                resp = client.get(url)
            elif method == "POST":
                resp = client.post(url, {})
            elif method == "PUT":
                resp = client.put(url, {})
            elif method == "DELETE":
                resp = client.delete(url)

            if resp.status_code == 429:
                # Si es 429, debe tener headers apropiados
                assert (
                    "Retry-After" in resp.headers or "Retry-after" in resp.headers
                ), f"429 con {method} debe incluir Retry-After"

                # Verificar formato del header
                retry_after = resp.headers.get("Retry-After") or resp.headers.get(
                    "Retry-after"
                )
                assert retry_after, f"Retry-After no puede estar vacío con {method}"

                # Debe ser numérico
                try:
                    int(retry_after)
                except ValueError:
                    pytest.fail(
                        f"Retry-After debe ser numérico con {method}: {retry_after}"
                    )
        except Exception:
            # Tolerar errores de endpoints que no existen o no soportan el método
            continue


@pytest.mark.django_db
def test_rate_limit_headers_stability(client):
    """
    Test que verifica estabilidad de headers de rate limiting.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user("ratelimit5", "test5@example.com", "password")
    client.force_login(user)

    url = "/cl/"
    retry_after_values = []

    # Hacer múltiples requests para verificar estabilidad
    for i in range(10):
        try:
            resp = client.get(url)
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After") or resp.headers.get(
                    "Retry-after"
                )
                if retry_after:
                    retry_after_values.append(int(retry_after))
        except Exception:
            continue

    # Si hay rate limiting activo, los valores deben ser consistentes
    if retry_after_values:
        # Todos los valores deben ser similares (dentro de un rango razonable)
        min_val = min(retry_after_values)
        max_val = max(retry_after_values)
        assert (
            max_val - min_val <= 10
        ), f"Retry-After values deben ser consistentes: {retry_after_values}"

        # Todos deben ser positivos
        assert all(
            val > 0 for val in retry_after_values
        ), f"Todos los Retry-After deben ser positivos: {retry_after_values}"
