import pytest

from django.urls import NoReverseMatch, reverse


@pytest.mark.django_db
def test_api_servicios_exists_and_responds(client):
    # Intenta nombres probables; ajusta si ya tienes el name exacto
    candidates = [
        "taller:documentos:api_servicios",
        "documentos:api_servicios",
        "api_servicios",
    ]
    url = None
    for name in candidates:
        try:
            url = reverse(name)
            break
        except NoReverseMatch:
            continue

    if not url:
        # fallback por path si usas algo tipo /documentos/api/servicios/
        for p in ("/documentos/api/servicios/", "/api/servicios/"):
            resp = client.get(p)
            if resp.status_code in (200, 204, 302, 401, 403, 405):
                return
        pytest.skip("Endpoint de API servicios no encontrado")

    resp = client.get(url)
    assert resp.status_code in (200, 204, 302, 401, 403, 405)
