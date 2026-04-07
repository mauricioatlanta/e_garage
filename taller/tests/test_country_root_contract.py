import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory

from taller.models import Empresa
from taller.views_root_country import country_lang_root_view


class _ResolverMatch:
    def __init__(self, namespace):
        self.namespace = namespace


@pytest.mark.django_db
def test_country_root_view_anon_us_en_redirects_to_public_bienvenida():
    request = RequestFactory().get("/us/en/")
    request.user = AnonymousUser()
    request.resolver_match = _ResolverMatch("us_en")

    response = country_lang_root_view(request)

    assert response.status_code in (301, 302)
    assert response.url == "/us/en/bienvenida/"


@pytest.mark.django_db
def test_country_root_view_authenticated_us_en_ready_redirects_to_workspace():
    user = User.objects.create_user(
        username="root-contract@example.com",
        email="root-contract@example.com",
        password="StrongPass123!",
    )
    Empresa.objects.create(
        user=user,
        nombre_taller="Root Contract Test",
        pais="US",
        onboarding_completado=True,
    )

    request = RequestFactory().get("/us/en/")
    request.user = user
    request.resolver_match = _ResolverMatch("us_en")
    request.session = {}

    response = country_lang_root_view(request)

    assert response.status_code in (301, 302)
    assert response.url == "/us/en/workspace/"


@pytest.mark.django_db
def test_country_root_view_authenticated_uruguay_es_without_empresa_redirects_to_onboarding():
    user = User.objects.create_user(
        username="uy-root-no-company@example.com",
        email="uy-root-no-company@example.com",
        password="StrongPass123!",
    )

    request = RequestFactory().get("/uy/es/")
    request.user = user
    request.resolver_match = _ResolverMatch("uruguay_es")
    request.session = {}

    response = country_lang_root_view(request)

    assert response.status_code in (301, 302)
    assert response.url == "/uy/es/onboarding/"


@pytest.mark.django_db
def test_country_root_view_authenticated_uruguay_es_ready_redirects_to_workspace():
    user = User.objects.create_user(
        username="uy-root-ready@example.com",
        email="uy-root-ready@example.com",
        password="StrongPass123!",
    )
    Empresa.objects.create(
        user=user,
        nombre_taller="Uruguay Root Test",
        pais="UY",
        onboarding_completado=True,
    )

    request = RequestFactory().get("/uy/es/")
    request.user = user
    request.resolver_match = _ResolverMatch("uruguay_es")
    request.session = {}

    response = country_lang_root_view(request)

    assert response.status_code in (301, 302)
    assert response.url == "/uy/es/workspace/"


@pytest.mark.django_db
def test_country_root_view_authenticated_argentina_without_empresa_redirects_to_onboarding():
    user = User.objects.create_user(
        username="ar-root-no-company@example.com",
        email="ar-root-no-company@example.com",
        password="StrongPass123!",
    )

    request = RequestFactory().get("/ar/")
    request.user = user
    request.resolver_match = _ResolverMatch("argentina")
    request.session = {}

    response = country_lang_root_view(request)

    assert response.status_code in (301, 302)
    assert response.url == "/ar/onboarding/"


@pytest.mark.django_db
def test_country_root_view_authenticated_argentina_ready_redirects_to_workspace():
    user = User.objects.create_user(
        username="ar-root-ready@example.com",
        email="ar-root-ready@example.com",
        password="StrongPass123!",
    )
    Empresa.objects.create(
        user=user,
        nombre_taller="Argentina Root Test",
        pais="AR",
        onboarding_completado=True,
    )

    request = RequestFactory().get("/ar/")
    request.user = user
    request.resolver_match = _ResolverMatch("argentina")
    request.session = {}

    response = country_lang_root_view(request)

    assert response.status_code in (301, 302)
    assert response.url == "/ar/workspace/"
