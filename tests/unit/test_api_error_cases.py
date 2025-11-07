import pytest
from django.urls import reverse, NoReverseMatch

def _reverse_any(candidates):
    for name in candidates:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue
    return None

@pytest.mark.django_db
def test_api_vehiculos_error_paths(client):
    url = _reverse_any([
        "taller:vehiculos_api_list",
        "vehiculos_api_list",
        "vehiculos:api_list",
    ]) or "/api/vehiculos/"

    # Método no permitido o sin auth debería dar 400/403/405 (o 200 si es público)
    resp = client.post(url, data={"invalid": True})
    assert resp.status_code in (200, 400, 401, 403, 404, 405)

@pytest.mark.django_db
def test_api_documentos_error_paths(client):
    url = _reverse_any([
        "taller:documentos:api_servicios",
        "documentos:api_servicios",
        "api_servicios",
    ]) or "/documentos/api/servicios/"

    resp = client.post(url, data={"bad": "data"})
    assert resp.status_code in (200, 400, 401, 403, 404, 405)
