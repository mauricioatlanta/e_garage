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
    for key in (
        "funnel",
        "crecimiento_global",
        "por_referrer",
        "mobile_share",
        "por_idioma",
        "eventos_funnel",
        "visitas_rafaga",
        "prospectos_estimados",
    ):
        assert key in resp.context_data, f"Falta clave en contexto: {key}"


@pytest.mark.django_db
def test_funnel_has_required_keys(rf, staff_user):
    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)
    funnel = resp.context_data["funnel"]
    for key in (
        "visitas",
        "sesiones_landing",
        "sesiones_utm",
        "empresas",
        "trials",
        "suscripciones",
        "tasa_conversion",
    ):
        assert key in funnel, f"Falta clave en funnel: {key}"
        assert isinstance(funnel[key], (int, float)), f"funnel['{key}'] debe ser numérico"


@pytest.mark.django_db
def test_eventos_funnel_groups_legacy_and_canonical_without_double_count(rf, staff_user):
    from taller.models.public_analytics_event import PublicAnalyticsEvent
    from taller.models.public_analytics_session import PublicAnalyticsSession
    from taller.services.public_attribution import hash_public_analytics_value
    from django.utils import timezone

    now = timezone.now()
    session = PublicAnalyticsSession.objects.create(
        anonymous_visitor_hash=hash_public_analytics_value("visitor"),
        anonymous_session_hash=hash_public_analytics_value("session"),
        first_path="/",
        last_path="/",
        landing_path="/",
        page_type="home",
        attribution_type=PublicAnalyticsSession.ATTRIBUTION_DIRECT,
        first_seen_at=now,
        last_seen_at=now,
        expires_at=now + timezone.timedelta(days=1),
    )
    for event_type in ("signup_start", "signup_started", "signup_complete", "signup_completed"):
        PublicAnalyticsEvent.objects.create(
            session=session,
            event_type=event_type,
            path="/accounts/signup/",
            dedupe_key=event_type,
        )
    PublicAnalyticsEvent.objects.create(
        session=session,
        event_type="cta_click",
        path="/",
        dedupe_key="/:country_cl",
    )
    PublicAnalyticsEvent.objects.create(
        session=session,
        event_type="cta_trial_30_click",
        path="/cl/desarmadurias/",
        dedupe_key="/cl/desarmadurias/:hero",
    )

    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)

    eventos = resp.context_data["eventos_funnel"]
    assert eventos["signup_starts"] == 1
    assert eventos["signup_completes"] == 1
    assert eventos["cta_clicks"] == 1


@pytest.mark.django_db
def test_prospectos_estimados_excludes_human_bursts(rf, staff_user):
    from taller.models.public_page_view import PublicPageView

    for index in range(21):
        PublicPageView.objects.create(
            path="/",
            page_type=PublicPageView.PAGE_HOME,
            visitor_hash="burst",
            user_agent="Mozilla/5.0",
            is_bot=False,
        )
    PublicPageView.objects.create(
        path="/",
        page_type=PublicPageView.PAGE_HOME,
        visitor_hash="single",
        user_agent="Mozilla/5.0",
        is_bot=False,
    )

    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)

    assert resp.context_data["humanos"] == 22
    assert resp.context_data["visitas_rafaga"] == 21
    assert resp.context_data["prospectos_estimados"] == 1
    assert resp.context_data["funnel"]["visitas"] == 1


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
def test_dashboard_separates_attributed_funnel_from_global_growth(rf, staff_user):
    from django.apps import apps
    from django.utils import timezone
    from taller.models.public_analytics_session import PublicAnalyticsSession
    from taller.models.public_page_view import PublicPageView
    from taller.services.public_attribution import hash_public_analytics_value

    Empresa = apps.get_model("taller", "Empresa")
    RegistroEmbudoSuscriptor = apps.get_model("taller", "RegistroEmbudoSuscriptor")

    user_demo = User.objects.create_user(
        username="seed_demo", email="seed@egarage.test", password="x"
    )
    user_real = User.objects.create_user(
        username="cliente_real", email="cliente@example.com", password="x"
    )
    user_attributed = User.objects.create_user(
        username="cliente_atribuido", email="atribuido@example.com", password="x"
    )
    Empresa.objects.create(user=user_demo, nombre_taller="Taller Prueba CL")
    Empresa.objects.create(user=user_real, nombre_taller="Taller Real S.A.")
    Empresa.objects.create(user=user_attributed, nombre_taller="Taller Atribuido S.A.", is_trial=True)
    now = timezone.now()
    session = PublicAnalyticsSession.objects.create(
        anonymous_visitor_hash=hash_public_analytics_value("visitor-dashboard"),
        anonymous_session_hash=hash_public_analytics_value("session-dashboard"),
        first_path="/cl/desarmadurias/",
        last_path="/cl/desarmadurias/",
        landing_path="/cl/desarmadurias/",
        country="cl",
        language="es",
        vertical_key="salvage",
        page_type=PublicPageView.PAGE_LANDING,
        attribution_type=PublicAnalyticsSession.ATTRIBUTION_DIRECT,
        first_seen_at=now,
        last_seen_at=now,
        expires_at=now + timezone.timedelta(days=1),
    )
    PublicPageView.objects.create(
        path="/cl/desarmadurias/",
        page_type=PublicPageView.PAGE_LANDING,
        visitor_hash="visitor-dashboard",
        public_session=session,
        user_agent="Mozilla/5.0",
        is_bot=False,
    )
    RegistroEmbudoSuscriptor.objects.create(
        user=user_attributed,
        public_session=session,
        pais="CL",
        fecha_registro=now,
        empresa_creada_at=now,
        obtuvo_trial=True,
    )

    request = rf.get("/analytics/public/")
    request.user = staff_user
    resp = public_analytics_dashboard(request)

    assert resp.context_data["crecimiento_global"]["empresas"] == 2
    assert resp.context_data["crecimiento_global"]["trials"] == 1
    assert resp.context_data["funnel"]["empresas"] == 1
    assert resp.context_data["funnel"]["trials"] == 1
    assert resp.context_data["funnel"]["sesiones_landing"] == 1
    assert resp.context_data["funnel"]["tasa_conversion"] == 100


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
