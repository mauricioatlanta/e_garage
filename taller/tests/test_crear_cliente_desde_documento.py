import pytest
from django.contrib.auth.models import User
from django.test import Client

from taller.models.empresa import Empresa


@pytest.fixture
@pytest.mark.django_db
def user_cl_empresa(db):
    user = User.objects.create_user(username="cl_user", password="testpass123")
    Empresa.objects.create(
        nombre_taller="Taller CL",
        pais="CL",
        user=user,
    )
    return user


@pytest.mark.django_db
def test_crear_cliente_modal_desde_documento_retorna_bridge(client: Client, user_cl_empresa):
    client.login(username="cl_user", password="testpass123")

    next_url = "http://testserver/cl/documentos/form/"
    response = client.post(
        "/cl/es/clientes/crear/",
        {
            "nombre": "Juan",
            "apellido": "Perez",
            "telefono": "+56911111111",
            "email": "juan.modal@test.com",
            "next": next_url,
            "modal": "1",
        },
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "eg:cliente-created" in content
    assert "Juan Perez" in content


@pytest.mark.django_db
def test_crear_cliente_ajax_desde_documento_retorna_json(client: Client, user_cl_empresa):
    client.login(username="cl_user", password="testpass123")

    response = client.post(
        "/cl/es/clientes/crear/",
        {
            "nombre": "Ana",
            "apellido": "Lopez",
            "telefono": "+56922222222",
            "email": "ana.ajax@test.com",
            "ajax": "1",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["cliente"]["nombre"] == "Ana Lopez"
    assert payload["cliente"]["id"]
