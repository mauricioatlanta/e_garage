from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.utils.whatsapp_helper import get_document_whatsapp_url


@pytest.mark.django_db
def test_budget_whatsapp_link_uses_public_approval_url():
    user = User.objects.create_user(username="wa-helper", password="pass")
    empresa = Empresa.objects.create(user=user, nombre_taller="Taller Link", pais="CL")
    cliente = Cliente.objects.create(
        empresa=empresa,
        nombre="Ana",
        apellido="Cliente",
        telefono="+56 9 1234 5678",
    )
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        tipo="PRES",
        estado="EMITIDO",
    )

    request = RequestFactory().get("/", secure=True, HTTP_HOST="egarage.cl")
    whatsapp_url = get_document_whatsapp_url(documento, request=request)

    assert whatsapp_url is not None
    assert whatsapp_url.startswith("https://wa.me/56912345678?text=")

    query = parse_qs(urlparse(whatsapp_url).query)
    message = query["text"][0]

    assert "aprobarlo online" in message
    assert f"/p/presupuesto/{documento.uuid}/" in message
