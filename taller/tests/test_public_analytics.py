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

from django.utils import timezone

from taller.analytics.public_views import admin_visits_dashboard, public_analytics_dashboard
from taller.models.public_page_view import PublicAnalyticsEvent, PublicPageView
from taller.services.public_analytics import track_public_page


class MutableSession(dict):
    modified = False


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


@pytest.mark.django_db
def test_admin_visits_dashboard_returns_200_for_staff(rf, staff_user):
    PublicPageView.objects.create(
        path="/cl/talleres/",
        page_type=PublicPageView.PAGE_LANDING,
        country="cl",
        language="es",
        visitor_hash="visitor-1",
        referrer="https://google.com/search",
        user_agent="Mozilla/5.0",
        is_mobile=True,
        is_bot=False,
        created_at=timezone.now(),
    )

    request = rf.get("/admin/visitas/?days=30")
    request.user = staff_user
    resp = admin_visits_dashboard(request)
    resp.render()

    assert resp.status_code == 200
    assert b"Adquisici" in resp.content
    assert resp.context_data["kpis"]["total_visits"] == 1
    assert resp.context_data["countries"][0]["country"] == "cl"
    assert resp.context_data["rubros"][0]["rubro"] == "workshop"


@pytest.mark.django_db
def test_admin_visits_dashboard_forbidden_for_regular_user(rf, regular_user):
    request = rf.get("/admin/visitas/")
    request.user = regular_user
    resp = admin_visits_dashboard(request)
    assert resp.status_code in (302, 403)


@pytest.mark.django_db
def test_admin_visits_dashboard_excludes_bots_by_default(rf, staff_user):
    now = timezone.now()
    PublicPageView.objects.create(
        path="/",
        page_type=PublicPageView.PAGE_HOME,
        country="cl",
        language="es",
        visitor_hash="human",
        is_bot=False,
        created_at=now,
    )
    PublicPageView.objects.create(
        path="/",
        page_type=PublicPageView.PAGE_HOME,
        country="cl",
        language="es",
        visitor_hash="bot",
        is_bot=True,
        created_at=now,
    )

    request = rf.get("/admin/visitas/?days=30")
    request.user = staff_user
    resp = admin_visits_dashboard(request)
    assert resp.context_data["kpis"]["total_visits"] == 1

    request = rf.get("/admin/visitas/?days=30&bots=1")
    request.user = staff_user
    resp = admin_visits_dashboard(request)
    assert resp.context_data["kpis"]["total_visits"] == 2


@pytest.mark.django_db
def test_admin_visits_dashboard_excludes_internal_traffic(rf, staff_user):
    PublicPageView.objects.create(
        path="/",
        page_type=PublicPageView.PAGE_HOME,
        country="cl",
        language="es",
        visitor_hash="server",
        is_internal=True,
        is_server=True,
        created_at=timezone.now(),
    )

    request = rf.get("/admin/visitas/?days=30")
    request.user = staff_user
    resp = admin_visits_dashboard(request)

    assert resp.context_data["kpis"]["total_visits"] == 0
    assert resp.context_data["kpis"]["excluded_internal"] == 1


@pytest.mark.django_db
def test_public_event_api_records_cta_click(client):
    resp = client.post(
        "/analytics/event/",
        data='{"event_type":"cta_click","label":"Prueba gratis","target":"/mx/es/accounts/signup/?rubro=workshop","rubro":"workshop","metadata":{"cta_kind":"free_trial_click","page_path":"/mx/es/desarmadurias/"}}',
        content_type="application/json",
        HTTP_USER_AGENT="Mozilla/5.0",
        HTTP_REFERER="https://facebook.com/post",
    )

    assert resp.status_code == 200
    event = PublicAnalyticsEvent.objects.get(event_type=PublicAnalyticsEvent.EVENT_CTA_CLICK)
    assert event.rubro == "workshop"
    assert event.country == "mx"
    assert event.language == "es"
    assert event.metadata["label"] == "Prueba gratis"
    assert event.metadata["cta_kind"] == "free_trial_click"


@pytest.mark.django_db
def test_track_public_page_infers_country_language_source_and_session(rf):
    request = rf.get(
        "/mx/es/desarmadurias/?utm_source=facebook&utm_medium=social&utm_campaign=fundadores_mx",
        HTTP_USER_AGENT="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        HTTP_ACCEPT_LANGUAGE="es-MX,es;q=0.9,en;q=0.6",
        HTTP_REFERER="https://l.facebook.com/story.php",
    )
    request.session = MutableSession()
    request.user = None
    request.LANGUAGE_CODE = ""

    page_view = track_public_page(
        request,
        page_type=PublicPageView.PAGE_LANDING,
    )

    assert page_view is not None
    assert page_view.country == "mx"
    assert page_view.language == "es"
    assert page_view.source_label == "facebook / social"
    assert page_view.utm_campaign == "fundadores_mx"
    assert page_view.landing_initial == "/mx/es/desarmadurias/"
    assert page_view.session_key
    assert page_view.is_mobile is True

    event = PublicAnalyticsEvent.objects.get(event_type=PublicAnalyticsEvent.EVENT_LANDING_VIEW)
    assert event.country == "mx"
    assert event.language == "es"
    assert event.rubro == "salvage"


@pytest.mark.django_db
def test_admin_visits_dashboard_exposes_entry_pages_ctas_and_languages(rf, staff_user):
    now = timezone.now()
    PublicPageView.objects.create(
        path="/cl/es/desarmadurias/",
        landing_initial="/cl/es/desarmadurias/",
        page_type=PublicPageView.PAGE_LANDING,
        country="cl",
        language="es",
        visitor_hash="visitor-cta",
        session_key="session-cta",
        source_label="instagram / social",
        is_mobile=True,
        is_bot=False,
        created_at=now,
    )
    PublicAnalyticsEvent.objects.create(
        event_type=PublicAnalyticsEvent.EVENT_CTA_CLICK,
        path="/cl/es/desarmadurias/",
        session_key="session-cta",
        visitor_hash="visitor-cta",
        country="cl",
        language="es",
        source_label="instagram / social",
        is_bot=False,
        metadata={"cta_kind": "whatsapp_click", "label": "WhatsApp"},
        created_at=now,
    )

    request = rf.get("/admin/visitas/?days=30")
    request.user = staff_user
    resp = admin_visits_dashboard(request)

    assert resp.context_data["entry_pages"][0]["path"] == "/cl/es/desarmadurias/"
    assert resp.context_data["cta_breakdown"][0]["label"] == "WhatsApp"
    assert resp.context_data["languages"][0]["language"] == "es"
    assert resp.context_data["device_rows"][0]["label"] == "Móvil"


@pytest.mark.django_db
def test_admin_visits_dashboard_exposes_campaign_channels(rf, staff_user):
    now = timezone.now()
    for source in ("facebook / social", "instagram / social", "Google", "Directo / sin referrer"):
        PublicPageView.objects.create(
            path="/cl/es/talleres/",
            page_type=PublicPageView.PAGE_LANDING,
            source_label=source,
            visitor_hash=f"visitor-{source}",
            session_key=f"session-{source}",
            is_bot=False,
            is_internal=False,
            created_at=now,
        )

    request = rf.get("/admin/visitas/?days=30")
    request.user = staff_user
    resp = admin_visits_dashboard(request)
    channels = {row["label"]: row["total"] for row in resp.context_data["campaign_channels"]}

    assert channels["Facebook"] == 1
    assert channels["Instagram"] == 1
    assert channels["Google"] == 1
    assert channels["Directo"] == 1


@pytest.mark.django_db
def test_admin_visits_dashboard_funnel_uses_only_attributed_events(rf, staff_user):
    from django.apps import apps

    Empresa = apps.get_model("taller", "Empresa")
    user_real = User.objects.create_user(
        username="cliente_embudo", email="cliente-embudo@example.com", password="x"
    )
    Empresa.objects.create(
        user=user_real,
        nombre_taller="Taller Embudo Real",
        suscripcion_activa=True,
        is_trial=False,
    )
    PublicPageView.objects.create(
        path="/cl/es/desarmadurias/",
        landing_initial="/cl/es/desarmadurias/",
        page_type=PublicPageView.PAGE_LANDING,
        country="cl",
        language="es",
        visitor_hash="visitor-landing",
        session_key="session-landing",
        source_label="whatsapp / direct",
        is_bot=False,
        is_internal=False,
        created_at=timezone.now(),
    )

    request = rf.get("/admin/visitas/?days=30")
    request.user = staff_user
    resp = admin_visits_dashboard(request)
    funnel = {row["key"]: row["value"] for row in resp.context_data["funnel_rows"]}

    assert resp.context_data["kpis"]["landing_visits"] == 1
    assert resp.context_data["kpis"]["new_companies"] == 1
    assert funnel[PublicAnalyticsEvent.EVENT_LANDING_VIEW] == 0
    assert funnel[PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETE] == 0
    assert funnel[PublicAnalyticsEvent.EVENT_SUBSCRIPTION_PAID] == 0
    assert resp.context_data["kpis"]["unattributed_companies"] == 1
    assert resp.context_data["kpis"]["unattributed_paid"] == 1
