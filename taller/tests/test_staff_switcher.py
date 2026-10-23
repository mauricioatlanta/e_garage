import pytest
from django.test import Client, RequestFactory

from taller.context_processors import company_country
from taller.context_processors.business_modules import business_modules
from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory, UserFactory


@pytest.mark.django_db
def test_superuser_can_apply_and_reset_support_environment():
    user = UserFactory(is_superuser=True, is_staff=True)
    EmpresaFactory(user=user)
    client = Client()
    client.force_login(user)

    response = client.post(
        "/staff/support-environment/",
        {"country": "br", "rubro": "REPUESTOS"},
        HTTP_REFERER="/cl/es/centro-operaciones/",
    )

    assert response.status_code == 302
    assert response["Location"] == "/cl/es/centro-operaciones/"
    assert client.session["support_country"] == "br"
    assert client.session["support_rubro"] == "PARTS"

    client.post(
        "/staff/support-environment/",
        {"action": "reset"},
        HTTP_REFERER="/cl/es/centro-operaciones/",
    )
    assert "support_country" not in client.session
    assert "support_rubro" not in client.session


@pytest.mark.django_db
def test_support_gruas_opens_dispatch_board():
    user = UserFactory(is_superuser=True, is_staff=True)
    EmpresaFactory(user=user)
    client = Client()
    client.force_login(user)

    response = client.post(
        "/staff/support-environment/",
        {"country": "cl", "rubro": "GRUAS"},
        HTTP_REFERER="/cl/es/documentos/",
    )

    assert response.status_code == 302
    assert response["Location"] == "/cl/es/gruas/"
    assert client.session["support_rubro"] == "TOWING"


@pytest.mark.django_db
def test_non_superuser_cannot_switch_support_environment():
    user = UserFactory()
    client = Client()
    client.force_login(user)

    response = client.post(
        "/staff/support-environment/",
        {"country": "us", "rubro": "TALLER"},
    )

    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_context_processors_use_support_values_without_mutating_company():
    empresa = EmpresaFactory(pais="CL")
    config = ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal="PARTS")
    user = empresa.user
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])

    request = RequestFactory().get("/cl/es/repuestos/")
    request.user = user
    request.empresa = empresa
    request.session = {"support_country": "mx", "support_rubro": "TIRE"}

    country_context = company_country(request)
    modules_context = business_modules(request)

    assert country_context["company_country"] == "MX"
    assert "repuestos" in modules_context["business_modules"]
    assert modules_context["product_profile"]["default_rubro"] == "TIRE"
    assert config.rubro_principal == "PARTS"
