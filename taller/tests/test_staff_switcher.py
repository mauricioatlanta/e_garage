from types import SimpleNamespace

import pytest
from django.http import HttpResponse
from django.test import Client, RequestFactory

from taller.context_processors import company_country
from taller.context_processors.business_modules import business_modules
from taller.middleware.lang_policy import LanguagePolicyMiddleware
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
def test_superuser_can_apply_multiple_support_rubros():
    user = UserFactory(is_superuser=True, is_staff=True)
    EmpresaFactory(user=user)
    client = Client()
    client.force_login(user)

    response = client.post(
        "/staff/support-environment/",
        {
            "country": "cl",
            "rubros": ["DESARMADURIA", "REPUESTOS"],
        },
        HTTP_REFERER="/cl/es/centro-operaciones/",
    )

    assert response.status_code == 302
    assert client.session["support_rubro"] == "DESARMADURIA"
    assert client.session["modo_soporte_rubros"] == ["DESARMADURIA", "PARTS"]

    request = RequestFactory().get("/cl/es/centro-operaciones/")
    request.user = user
    request.session = client.session
    context = business_modules(request)
    assert "desarme" in context["business_modules"]
    assert "repuestos" in context["business_modules"]


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


@pytest.mark.django_db
def test_superuser_switch_to_us_sets_english_cookie_session_and_us_en_url():
    user = UserFactory(is_superuser=True, is_staff=True)
    EmpresaFactory(user=user)
    client = Client()
    client.force_login(user)

    response = client.post(
        "/staff/support-environment/",
        {"country": "us", "rubro": "TALLER"},
        HTTP_REFERER="/cl/es/centro-operaciones/",
    )

    assert response.status_code == 302
    assert response["Location"] == "/us/en/centro-operaciones/"
    assert client.session["support_country"] == "us"
    assert client.session["django_language"] == "en"
    assert client.session["preferred_lang"] == "en"
    assert response.cookies["django_language"].value == "en"


def test_lang_policy_uses_support_country_for_superuser():
    middleware = LanguagePolicyMiddleware(lambda request: HttpResponse(status=200))
    request = SimpleNamespace(
        user=SimpleNamespace(is_superuser=True),
        session={"support_country": "US"},
        empresa=SimpleNamespace(pais="CL"),
        COOKIES={},
        path="/cl/es/centro-operaciones/",
    )

    middleware(request)

    assert request.LANGUAGE_CODE == "en"
