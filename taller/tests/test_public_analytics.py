"""
Tests del dashboard de analytics público de eGarage.

Cubre:
1. Respuesta HTTP 200 para staff.
2. Contexto contiene las variables de Fase 5 y Fase 8.
3. Funnel tiene las claves esperadas con valores enteros.
4. 403 para usuario no-staff.
5. home_humanas presente en contexto.
6. tendencia usa humanos/bots (no total).
7. empresas_por_dia presente en contexto.
8. Funnel excluye cuentas demo (@egarage.test / nombre "prueba|demo").
9. empresas_por_dia excluye cuentas demo.
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


@pytest.mark.django_db
def test_home_kpi_in_context(rf, staff_user):
    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)
    assert "home_humanas" in resp.context_data
    assert isinstance(resp.context_data["home_humanas"], int)


@pytest.mark.django_db
def test_tendencia_has_bots_split(rf, staff_user):
    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)
    rows = list(resp.context_data["tendencia"])
    if rows:
        assert "humanos" in rows[0], "tendencia debe tener clave 'humanos'"
        assert "bots" in rows[0], "tendencia debe tener clave 'bots'"
        assert "total" not in rows[0], "tendencia no debe usar 'total' (fue reemplazado)"


@pytest.mark.django_db
def test_empresas_por_dia_present(rf, staff_user):
    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)
    assert "empresas_por_dia" in resp.context_data


@pytest.mark.django_db
def test_funnel_excludes_demo_companies(rf, staff_user):
    from django.apps import apps
    Empresa = apps.get_model("taller", "Empresa")

    user_demo = User.objects.create_user(
        username="seed_demo", email="seed@egarage.test", password="x"
    )
    user_real = User.objects.create_user(
        username="cliente_real", email="cliente@example.com", password="x"
    )
    Empresa.objects.create(user=user_demo, nombre_taller="Taller Prueba CL")
    Empresa.objects.create(user=user_real, nombre_taller="Taller Real S.A.")

    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)

    assert resp.context_data["funnel"]["empresas"] == 1


@pytest.mark.django_db
def test_empresas_por_dia_excludes_demo_companies(rf, staff_user):
    from django.apps import apps
    Empresa = apps.get_model("taller", "Empresa")

    user_demo = User.objects.create_user(
        username="vc_seed", email="demo@egarage.test", password="x"
    )
    Empresa.objects.create(user=user_demo, nombre_taller="Demo Taller AutoShop")

    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)

    assert list(resp.context_data["empresas_por_dia"]) == []
