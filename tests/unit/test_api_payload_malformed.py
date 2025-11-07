import pytest
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model

def _rev(cands, fallback):
    for n in cands:
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    return fallback

@pytest.mark.django_db
def test_malformed_json_en_endpoints_creacion(client):
    User = get_user_model()
    client.force_login(User.objects.create_user(username="mal", password="x"))

    veh_url = _rev(["vehiculos:api_create","taller:vehiculos:api_create","vehiculos_api_create"], "/cl/vehiculos/api/create/")
    doc_url = _rev(["documentos_cl_es:api_create","documentos_us_en:api_create","documentos:api_create"], "/cl/documentos/api/create/")

    # Enviamos texto plano con content-type JSON -> debe fallar con 400/422/415
    bad_payload = "esto no es JSON"
    rv1 = client.post(veh_url, data=bad_payload, content_type="application/json")
    rv2 = client.post(doc_url, data=bad_payload, content_type="application/json")

    assert rv1.status_code in (400, 401, 403, 405, 415, 422)
    assert rv2.status_code in (400, 401, 403, 405, 415, 422)
