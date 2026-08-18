"""
Tests del dashboard de analytics público de eGarage.

Cubre:
1. Respuesta HTTP 200 para staff.
2. Contexto contiene las 4 variables nuevas.
3. Funnel tiene las claves esperadas con valores enteros.
4. 403 para usuario no-staff.
"""
import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from taller.analytics.public_views import public_analytics_dashboard


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="staff_test", password="pass", is_staff=True, is_superuser=True
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="regular_test", password="pass")


@pytest.mark.django_db
def test_dashboard_returns_200_for_staff(rf, staff_user):
    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_dashboard_context_has_new_variables(rf, staff_user):
    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)
    assert resp.status_code == 200
    for key in ("funnel", "por_referrer", "mobile_share", "por_idioma"):
        assert key in resp.context_data, f"Falta clave en contexto: {key}"


@pytest.mark.django_db
def test_funnel_has_required_keys(rf, staff_user):
    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)
    funnel = resp.context_data["funnel"]
    for key in ("visitas", "empresas", "trials", "suscripciones"):
        assert key in funnel, f"Falta clave en funnel: {key}"
        assert isinstance(funnel[key], int), f"funnel['{key}'] debe ser int"


@pytest.mark.django_db
def test_dashboard_forbidden_for_regular_user(rf, regular_user):
    request = rf.get("/analytics/public/")
    request.user = regular_user
    resp = public_analytics_dashboard(request)
    assert resp.status_code in (302, 403)
