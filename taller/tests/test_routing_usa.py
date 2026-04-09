import pytest
from allauth.account.models import EmailAddress
from django.urls import resolve
from django.contrib.auth.models import User
from django.core.management import call_command

from taller.models import Empresa


@pytest.mark.django_db
def test_us_en_root_resolves_and_redirects(client):
    match = resolve("/us/en/")
    assert match.view_name == "us_en:root"

    response = client.get("/us/en/", follow=False)
    assert response.status_code in (301, 302)
    assert response.headers["Location"].endswith("/us/en/bienvenida/")


@pytest.mark.django_db
def test_us_es_root_resolves_and_redirects(client):
    match = resolve("/us/es/")
    assert match.view_name == "us_es:root"

    response = client.get("/us/es/", follow=False)
    assert response.status_code in (301, 302)
    assert response.headers["Location"].endswith("/us/es/bienvenida/")


@pytest.mark.django_db
def test_us_login_pages_do_not_crash(client):
    response_en = client.get("/us/en/accounts/login/")
    response_es = client.get("/us/es/accounts/login/")

    assert response_en.status_code == 200
    assert response_es.status_code == 200


@pytest.mark.django_db
def test_us_bienvenida_pages_do_not_crash(client):
    response_en = client.get("/us/en/bienvenida/")
    response_es = client.get("/us/es/bienvenida/")

    assert response_en.status_code == 200
    assert response_es.status_code == 200


@pytest.mark.django_db
def test_us_demo_route_is_available_under_country_namespaces(client):
    response_en = client.get("/us/en/demo/atlanta/")
    response_es = client.get("/us/es/demo/atlanta/")

    assert response_en.status_code == 200
    assert response_es.status_code == 200


@pytest.mark.django_db
def test_us_en_root_authenticated_company_ready_redirects_to_workspace(client):
    user = User.objects.create_user(
        username="us-root@example.com",
        email="us-root@example.com",
        password="StrongPass123!",
    )
    Empresa.objects.create(
        user=user,
        nombre_taller="USA Root Test",
        pais="US",
        onboarding_completado=True,
    )

    client.force_login(user)
    response = client.get("/us/en/", follow=False)

    assert response.status_code in (301, 302)
    assert response.headers["Location"].endswith("/us/en/workspace/")


@pytest.mark.django_db
def test_legacy_us_root_redirects_to_canonical_en(client):
    response = client.get("/us/", follow=False)
    assert response.status_code in (301, 302)
    assert response.headers["Location"] == "/us/en/"


@pytest.mark.django_db
def test_legacy_us_login_redirects_to_canonical_en(client):
    response = client.get("/us/accounts/login/", follow=False)
    assert response.status_code in (301, 302)
    assert response.headers["Location"].rstrip("/") == "/us/en/accounts/login"


@pytest.mark.django_db
def test_legacy_us_dashboard_redirects_to_canonical_en(client):
    response = client.get("/us/dashboard/", follow=False)
    assert response.status_code in (301, 302)
    assert response.headers["Location"].rstrip("/") == "/us/en/dashboard"


@pytest.mark.django_db
def test_ensure_demo_accounts_marks_usa_email_verified_and_login_works(client):
    call_command("ensure_demo_accounts", username=["testuser_usa"])

    user = User.objects.get(username="testuser_usa")
    email = EmailAddress.objects.get(user=user, email="testuser@usa-garage.com")

    assert email.verified is True
    assert email.primary is True

    response = client.post(
        "/us/en/accounts/login/",
        {"login": "testuser@usa-garage.com", "password": "TestUSA2025!"},
        follow=False,
    )

    assert response.status_code in (302, 303)
    assert response.headers["Location"] != "/accounts/confirm-email/"
    assert response.headers["Location"].startswith("/us/en/")
