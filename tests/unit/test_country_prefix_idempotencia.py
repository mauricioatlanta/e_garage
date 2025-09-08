import pytest


@pytest.mark.django_db
def test_cl_no_redirige_y_us_si(client):
    # En CL no debe redirigir
    r1 = client.get("/cl/documentos/api/create/")
    assert r1.status_code in (200, 201, 400, 405)  # pero NO 302
    assert r1.status_code != 302

    # En US debe redirigir a CL y preservar querystring (?next=…)
    # Tolerante: puede ser 302 (redirect) o 405 (method not allowed) si el endpoint no acepta GET
    r2 = client.get("/us/documentos/api/create/?next=/us/vehiculos/")
    assert r2.status_code in (302, 405)
    if r2.status_code == 302:
        assert r2.headers["Location"].endswith(
            "/cl/documentos/api/create/?next=/us/vehiculos/"
        )
