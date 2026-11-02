from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa


@pytest.fixture
def public_budget(db):
    from taller.tests.factories import EmpresaFactory
    empresa = EmpresaFactory(nombre_taller="Taller Publico", pais="CL")
    cliente = Cliente.objects.create(
        empresa=empresa,
        nombre="Mario",
        apellido="Suarez",
        telefono="+56 9 8765 4321",
        email="mario@example.com",
    )
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        tipo="PRES",
        estado="EMITIDO",
        total=150000,
    )
    return documento


@pytest.mark.django_db
def test_public_budget_detail_is_available_without_login(client, public_budget):
    url = reverse("publico:ver_presupuesto", kwargs={"uuid": public_budget.uuid})

    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode()
    assert "Mario Suarez" in content
    assert "APROBAR PRESUPUESTO" in content


@pytest.mark.django_db
@patch("taller.views_extra.public_views.notificar_aprobacion_taller")
def test_public_budget_approval_records_timestamp_and_ip(mock_notify, client, public_budget):
    url = reverse("publico:aprobar_presupuesto", kwargs={"uuid": public_budget.uuid})

    response = client.post(url, follow=True)
    public_budget.refresh_from_db()

    assert response.status_code == 200
    assert public_budget.approved_at is not None
    assert public_budget.approved_by == "Mario Suarez"
    assert public_budget.approved_ip == "127.0.0.1"
    mock_notify.assert_called_once_with(public_budget)
