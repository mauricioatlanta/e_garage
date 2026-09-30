from datetime import timedelta
from pathlib import Path
import uuid
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db import IntegrityError, transaction
from django.test import Client, override_settings
from django.utils import timezone

from taller.models.public_analytics_event import PublicAnalyticsEvent
from taller.models.public_analytics_session import PublicAnalyticsSession
from taller.models.public_page_view import PublicPageView
from taller.models.registro_embudo import RegistroEmbudoSuscriptor
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.services.public_attribution import (
    find_first_touch_session_for_request,
    get_or_create_public_session,
    hash_public_analytics_value,
)
from taller.services.public_event_tracking import record_signup_completed_from_request
from taller.services.public_event_tracking import record_company_created_for_user
from taller.services.public_event_tracking import record_first_login_for_user
from taller.services.public_event_tracking import is_internal_first_login_request
from taller.services.registro_embudo_service import registrar_signup
from taller.services.registro_embudo_service import registrar_empresa_creada
from taller.tests.factories import EmpresaFactory


pytestmark = pytest.mark.django_db
CSRF_TOKEN = "a" * 32


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


def _csrf_client():
    client = Client(enforce_csrf_checks=True)
    client.cookies["csrftoken"] = CSRF_TOKEN
    return client


def _post_event(client, payload, **headers):
    return client.post(
        "/analytics/public/event/",
        data=payload,
        content_type="application/json",
        HTTP_X_CSRFTOKEN=CSRF_TOKEN,
        **headers,
    )


def _scroll_payload(dedupe_key="csrf-scroll"):
    return {
        "event_type": "scroll_50",
        "path": "/cl/desarmadurias/",
        "dedupe_key": dedupe_key,
        "metadata": {"scroll_percent": 50, "viewport_height": 800},
    }


def _make_attributed_session(visitor_cookie, **overrides):
    now = timezone.now()
    raw_session = uuid.uuid4().hex
    values = {
        "anonymous_visitor_hash": hash_public_analytics_value(visitor_cookie),
        "anonymous_session_hash": hash_public_analytics_value(raw_session),
        "first_path": "/cl/desarmadurias/",
        "last_path": "/cl/desarmadurias/",
        "landing_path": "/cl/desarmadurias/",
        "country": "cl",
        "language": "es",
        "vertical_key": "salvage",
        "page_type": "landing",
        "attribution_type": PublicAnalyticsSession.ATTRIBUTION_DIRECT,
        "first_seen_at": now - timedelta(minutes=5),
        "last_seen_at": now - timedelta(minutes=5),
        "expires_at": now + timedelta(days=25),
        "is_bot": False,
        "is_internal": False,
    }
    values.update(overrides)
    return PublicAnalyticsSession.objects.create(**values)


def _signup_for_visitor(visitor_cookie):
    client = Client()
    client.cookies["eg_visitor_id"] = visitor_cookie
    response = client.get("/accounts/signup/?rubro=DESARMADURIA")
    return client, response


def test_general_settings_do_not_hardcode_public_analytics_test_key():
    base_dir = Path(settings.BASE_DIR)
    general_settings = [
        base_dir / "gestion_taller" / "settings.py",
        base_dir / "gestion_taller" / "settings" / "__init__.py",
        base_dir / "gestion_taller" / "settings" / "base.py",
        base_dir / "gestion_taller" / "settings_prod.py",
    ]

    for path in general_settings:
        assert "test-public-analytics-key" not in path.read_text()


def test_test_settings_define_deterministic_public_analytics_key():
    assert settings.PUBLIC_ANALYTICS_HASH_KEY == "test-public-analytics-key"


def test_test_settings_define_qa_email_domain():
    assert settings.PUBLIC_ANALYTICS_QA_EMAIL_DOMAIN == "egarage.test"


@override_settings(PUBLIC_ANALYTICS_HASH_KEY="")
def test_missing_public_analytics_hash_key_does_not_block_landing_or_create_session():
    client = Client()

    response = client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    assert response.status_code == 200
    assert PublicPageView.objects.filter(path="/cl/desarmadurias/").count() == 1
    assert PublicAnalyticsSession.objects.count() == 0
    assert "eg_visitor_id" not in response.cookies
    assert "eg_session_id" not in response.cookies


def test_landing_creates_public_session_and_preserves_public_page_view():
    client = Client()

    response = client.get(
        "/cl/desarmadurias/?utm_source=google&utm_campaign=salvage",
        HTTP_USER_AGENT="Mozilla/5.0",
    )

    assert response.status_code == 200
    assert "eg_visitor_id" in response.cookies
    assert "eg_session_id" in response.cookies

    page_view = PublicPageView.objects.get(path="/cl/desarmadurias/")
    assert page_view.public_session is not None
    assert page_view.public_session.utm_source == "google"
    assert page_view.public_session.utm_campaign == "salvage"
    assert page_view.public_session.vertical_key == "salvage"


def test_public_page_view_visitor_hash_uses_secret_hmac():
    first = PublicPageView.build_visitor_hash(
        ip="203.0.113.10",
        user_agent="Mozilla/5.0",
        date_key="2026-09-29",
    )

    with override_settings(PUBLIC_ANALYTICS_HASH_KEY="different-public-analytics-key"):
        second = PublicPageView.build_visitor_hash(
            ip="203.0.113.10",
            user_agent="Mozilla/5.0",
            date_key="2026-09-29",
        )

    assert first != second
    assert len(first) == 64


def test_public_session_accepts_long_utm_values_up_to_model_limit():
    client = Client()
    long_source = "source-" + ("x" * 249)
    longer_campaign = "campaign-" + ("y" * 320)

    response = client.get(
        f"/cl/desarmadurias/?utm_source={long_source}&utm_campaign={longer_campaign}",
        HTTP_USER_AGENT="Mozilla/5.0",
    )

    assert response.status_code == 200
    session = PublicAnalyticsSession.objects.get()
    assert session.utm_source == long_source[:255]
    assert session.utm_campaign == longer_campaign[:255]


def test_desarmaduria_landing_sets_real_csrf_cookie_and_endpoint_accepts_it():
    client = Client(enforce_csrf_checks=True)

    landing = client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")
    csrf_token = landing.cookies["csrftoken"].value
    event = client.post(
        "/analytics/public/event/",
        data=_scroll_payload("real-csrf"),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert landing.status_code == 200
    assert csrf_token
    assert event.status_code == 200
    assert event.json()["created"] is True


def test_gateway_sets_real_csrf_cookie_and_endpoint_accepts_cta_click():
    client = Client(enforce_csrf_checks=True)

    gateway = client.get("/", HTTP_USER_AGENT="Mozilla/5.0")
    csrf_token = gateway.cookies["csrftoken"].value
    event = client.post(
        "/analytics/public/event/",
        data={
            "event_type": "cta_click",
            "path": "/",
            "dedupe_key": "/:country_cl",
            "metadata": {
                "cta_id": "country_cl",
                "cta_label": "eGarage Chile",
                "href": "/cl/",
            },
        },
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert gateway.status_code == 200
    assert csrf_token
    assert event.status_code == 200
    assert event.json()["created"] is True
    assert PublicAnalyticsEvent.objects.filter(event_type="cta_click").count() == 1


def test_other_rubro_does_not_activate_csrf_instrumentation_cookie():
    client = Client(enforce_csrf_checks=True)

    response = client.get("/cl/talleres/", HTTP_USER_AGENT="Mozilla/5.0")

    assert response.status_code == 200
    assert "csrftoken" not in response.cookies
    assert "/static/public/js/public_funnel_tracking.js" not in response.content.decode()


def test_gateway_instruments_country_ctas_without_public_funnel_script():
    client = Client()

    response = client.get("/", HTTP_USER_AGENT="Mozilla/5.0")
    html = response.content.decode()

    assert response.status_code == 200
    assert "data-public-gateway-cta=" in html
    assert 'event_type: "cta_click"' in html
    assert 'path: "/"' in html
    assert "/analytics/public/event/" in html
    assert "/static/public/js/public_funnel_tracking.js" not in html


def test_desarmaduria_landing_loads_public_funnel_tracking_only_there():
    client = Client()

    desarmaduria = client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")
    talleres = client.get("/cl/talleres/", HTTP_USER_AGENT="Mozilla/5.0")

    desarmaduria_html = desarmaduria.content.decode()
    talleres_html = talleres.content.decode()

    assert desarmaduria.status_code == 200
    assert "/static/public/js/public_funnel_tracking.js" in desarmaduria_html
    assert desarmaduria_html.count("data-public-funnel-trial-cta=") == 3
    assert "/static/public/js/public_funnel_tracking.js" not in talleres_html
    assert "data-public-funnel-trial-cta=" not in talleres_html


def test_public_funnel_tracking_js_uses_fetch_csrf_keepalive_without_sendbeacon():
    script = (Path(settings.BASE_DIR) / "static" / "public" / "js" / "public_funnel_tracking.js").read_text()

    assert 'TRACKED_PATH = "/cl/desarmadurias/"' in script
    assert "window.fetch" in script
    assert '"X-CSRFToken": csrfToken' in script
    assert 'credentials: "same-origin"' in script
    assert "keepalive: true" in script
    assert "requestAnimationFrame" in script
    assert "scrollFramePending" in script
    assert "scrollHeight <= viewportHeight" in script
    assert 'document.addEventListener("click", handleTrialClick)' in script
    assert script.count('addEventListener("click"') == 1
    assert 'closest("[data-public-funnel-trial-cta]")' in script
    assert "preventDefault" not in script
    assert "sendBeacon" not in script


def test_event_endpoint_requires_post_and_csrf():
    client = Client(enforce_csrf_checks=True)

    assert client.get("/analytics/public/event/").status_code == 405
    assert client.post(
        "/analytics/public/event/",
        data={},
        content_type="application/json",
    ).status_code == 403


def test_event_endpoint_rejects_non_json_content_type():
    client = _csrf_client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    text_plain = client.post(
        "/analytics/public/event/",
        data='{"event_type":"scroll_50","path":"/cl/desarmadurias/"}',
        content_type="text/plain",
        HTTP_X_CSRFTOKEN=CSRF_TOKEN,
    )
    form_encoded = client.post(
        "/analytics/public/event/",
        data={"event_type": "scroll_50", "path": "/cl/desarmadurias/"},
        HTTP_X_CSRFTOKEN=CSRF_TOKEN,
    )

    assert text_plain.status_code == 415
    assert text_plain.json()["error"] == "unsupported_media_type"
    assert form_encoded.status_code == 415
    assert form_encoded.json()["error"] == "unsupported_media_type"


def test_event_endpoint_accepts_valid_desarmaduria_event_once():
    client = _csrf_client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    payload = {
        "event_type": "scroll_50",
        "path": "/cl/desarmadurias/",
        "dedupe_key": "/cl/desarmadurias/:scroll_50",
        "metadata": {"scroll_percent": 50, "viewport_height": 800},
    }

    first = _post_event(client, payload)
    second = _post_event(client, payload)

    assert first.status_code == 200
    assert first.json()["created"] is True
    assert second.status_code == 200
    assert second.json()["created"] is False
    assert PublicAnalyticsEvent.objects.filter(event_type="scroll_50").count() == 1


def test_public_event_dedupe_is_enforced_by_database_constraint():
    session = _make_attributed_session(uuid.uuid4().hex)
    event_data = {
        "session": session,
        "event_type": PublicAnalyticsEvent.EVENT_SCROLL_50,
        "path": "/cl/desarmadurias/",
        "dedupe_key": "/cl/desarmadurias/:scroll_50",
    }

    PublicAnalyticsEvent.objects.create(**event_data)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PublicAnalyticsEvent.objects.create(**event_data)


def test_other_rubros_do_not_generate_desarmaduria_events():
    client = _csrf_client()
    client.get("/cl/talleres/", HTTP_USER_AGENT="Mozilla/5.0")

    assert PublicAnalyticsSession.objects.count() == 0
    assert PublicPageView.objects.get(path="/cl/talleres/").public_session is None

    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    response = _post_event(
        client,
        {
            "event_type": "scroll_50",
            "path": "/cl/talleres/",
            "dedupe_key": "/cl/talleres/:scroll_50",
            "metadata": {"scroll_percent": 50},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "path_not_allowed"
    assert PublicAnalyticsEvent.objects.exclude(event_type="human_visit").count() == 0


def test_event_endpoint_rejects_manipulated_sensitive_fields():
    client = _csrf_client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    response = _post_event(
        client,
        {
            "event_type": "scroll_50",
            "path": "/cl/desarmadurias/",
            "is_bot": False,
            "vertical_key": "salvage",
            "metadata": {"scroll_percent": 50},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "sensitive_client_fields_rejected"


def test_public_endpoint_rejects_signup_started():
    client = _csrf_client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    response = _post_event(
        client,
        {
            "event_type": "signup_started",
            "path": "/cl/desarmadurias/",
            "metadata": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "event_type_not_allowed"


def test_public_endpoint_rejects_signup_completed():
    client = _csrf_client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    response = _post_event(
        client,
        {
            "event_type": "signup_completed",
            "path": "/accounts/signup/",
            "metadata": {"source": "frontend"},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "event_type_not_allowed"


def test_event_endpoint_rejects_invalid_event_type_and_excessive_metadata():
    client = _csrf_client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    invalid = _post_event(
        client,
        {"event_type": "demo_requested", "path": "/cl/desarmadurias/"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"] == "event_type_not_allowed"

    excessive = _post_event(
        client,
        {
            "event_type": "scroll_50",
            "path": "/cl/desarmadurias/",
            "metadata": {"scroll_percent": "x" * 2000},
        },
    )
    assert excessive.status_code == 413
    assert excessive.json()["error"] == "metadata_too_large"


@pytest.mark.parametrize("user_flags", [{"is_staff": True}, {"is_superuser": True}])
def test_staff_and_superuser_sessions_are_internal(rf, django_user_model, user_flags):
    user = django_user_model.objects.create_user(
        username=f"internal_{list(user_flags)[0]}",
        password="pass",
        **user_flags,
    )
    request = rf.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")
    request.user = user

    session = get_or_create_public_session(
        request,
        page_type=PublicPageView.PAGE_LANDING,
        country="cl",
        language="es",
    )

    assert session is not None
    assert session.is_internal is True


@override_settings(PUBLIC_ANALYTICS_EXCLUDED_IPS=["159.223.200.106"])
def test_excluded_server_ip_is_marked_internal_and_does_not_create_human_visit_event():
    client = Client()

    response = client.get(
        "/cl/desarmadurias/",
        HTTP_USER_AGENT="Mozilla/5.0",
        REMOTE_ADDR="159.223.200.106",
    )

    assert response.status_code == 200
    session = PublicAnalyticsSession.objects.get()
    page_view = PublicPageView.objects.get(path="/cl/desarmadurias/")
    assert session.is_internal is True
    assert page_view.public_session_id == session.pk
    assert page_view.is_internal is True
    assert PublicAnalyticsEvent.objects.filter(event_type="human_visit").count() == 0


@override_settings(PUBLIC_ANALYTICS_RATE_LIMIT_ATTEMPTS=1, PUBLIC_ANALYTICS_RATE_LIMIT_WINDOW=60)
def test_event_endpoint_uses_shared_cache_rate_limit():
    client = _csrf_client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")
    payload = {
        "event_type": "scroll_50",
        "path": "/cl/desarmadurias/",
        "dedupe_key": "rl-1",
        "metadata": {"scroll_percent": 50},
    }

    assert _post_event(client, payload).status_code == 200
    limited = _post_event(client, {**payload, "dedupe_key": "rl-2"})

    assert limited.status_code == 429
    assert limited.json()["error"] == "rate_limit_exceeded"


def test_event_endpoint_handles_blocked_cookies_without_crashing():
    client = _csrf_client()

    response = _post_event(
        client,
        {
            "event_type": "scroll_50",
            "path": "/cl/desarmadurias/",
            "metadata": {"scroll_percent": 50},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "session_required"


def test_first_touch_uses_oldest_attributed_session_within_30_days(rf):
    client = Client()
    client.get(
        "/cl/desarmadurias/?utm_source=google&utm_campaign=first",
        HTTP_USER_AGENT="Mozilla/5.0",
    )
    first = PublicAnalyticsSession.objects.get(utm_campaign="first")
    old_time = timezone.now() - timedelta(minutes=31)
    PublicAnalyticsSession.objects.filter(pk=first.pk).update(last_seen_at=old_time)

    client.get(
        "/cl/desarmadurias/?utm_source=meta&utm_campaign=second",
        HTTP_USER_AGENT="Mozilla/5.0",
    )

    request = rf.get("/accounts/signup/")
    request.COOKIES["eg_visitor_id"] = client.cookies["eg_visitor_id"].value

    attributed = find_first_touch_session_for_request(request)
    assert attributed.pk == first.pk
    assert attributed.utm_campaign == "first"


def test_signup_started_filters_talleres_before_selecting_first_touch():
    visitor_cookie = uuid.uuid4().hex
    talleres = _make_attributed_session(
        visitor_cookie,
        first_path="/cl/talleres/",
        last_path="/cl/talleres/",
        landing_path="/cl/talleres/",
        vertical_key="workshop",
        first_seen_at=timezone.now() - timedelta(minutes=10),
        last_seen_at=timezone.now() - timedelta(minutes=10),
    )
    salvage = _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() - timedelta(minutes=5),
        last_seen_at=timezone.now() - timedelta(minutes=5),
    )

    _client, response = _signup_for_visitor(visitor_cookie)

    assert response.status_code == 200
    event = PublicAnalyticsEvent.objects.get(event_type="signup_started")
    assert event.session_id == salvage.pk
    assert event.session_id != talleres.pk
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_started").count() == 1


def test_signup_started_selects_oldest_valid_salvage_session():
    visitor_cookie = uuid.uuid4().hex
    oldest = _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() - timedelta(minutes=10),
        last_seen_at=timezone.now() - timedelta(minutes=10),
    )
    newer = _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() - timedelta(minutes=5),
        last_seen_at=timezone.now() - timedelta(minutes=5),
    )

    _client, response = _signup_for_visitor(visitor_cookie)

    assert response.status_code == 200
    event = PublicAnalyticsEvent.objects.get(event_type="signup_started")
    assert event.session_id == oldest.pk
    assert event.session_id != newer.pk


def test_signup_started_not_created_for_talleres_only():
    visitor_cookie = uuid.uuid4().hex
    _make_attributed_session(
        visitor_cookie,
        first_path="/cl/talleres/",
        last_path="/cl/talleres/",
        landing_path="/cl/talleres/",
        vertical_key="workshop",
    )

    _client, response = _signup_for_visitor(visitor_cookie)

    assert response.status_code == 200
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_started").count() == 0


@pytest.mark.parametrize(
    ("country", "vertical_key"),
    [("us", "salvage"), ("cl", "workshop")],
)
def test_signup_started_rejects_wrong_country_or_vertical(country, vertical_key):
    visitor_cookie = uuid.uuid4().hex
    _make_attributed_session(visitor_cookie, country=country, vertical_key=vertical_key)

    _client, response = _signup_for_visitor(visitor_cookie)

    assert response.status_code == 200
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_started").count() == 0


@pytest.mark.parametrize(
    ("landing_path", "first_path"),
    [
        ("/cl/talleres/", "/cl/desarmadurias/"),
        ("/cl/desarmadurias/", "/cl/talleres/"),
    ],
)
def test_signup_started_accepts_either_valid_attribution_path(landing_path, first_path):
    visitor_cookie = uuid.uuid4().hex
    session = _make_attributed_session(
        visitor_cookie,
        landing_path=landing_path,
        first_path=first_path,
    )

    _client, response = _signup_for_visitor(visitor_cookie)

    assert response.status_code == 200
    event = PublicAnalyticsEvent.objects.get(event_type="signup_started")
    assert event.session_id == session.pk


def test_signup_started_rejects_session_older_than_attribution_window():
    visitor_cookie = uuid.uuid4().hex
    _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() - timedelta(days=31),
        last_seen_at=timezone.now() - timedelta(days=31),
    )

    _client, response = _signup_for_visitor(visitor_cookie)

    assert response.status_code == 200
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_started").count() == 0


def test_signup_started_ignores_older_bot_and_internal_sessions():
    visitor_cookie = uuid.uuid4().hex
    bot = _make_attributed_session(
        visitor_cookie,
        is_bot=True,
        first_seen_at=timezone.now() - timedelta(minutes=10),
        last_seen_at=timezone.now() - timedelta(minutes=10),
    )
    internal = _make_attributed_session(
        visitor_cookie,
        is_internal=True,
        first_seen_at=timezone.now() - timedelta(minutes=9),
        last_seen_at=timezone.now() - timedelta(minutes=9),
    )
    valid = _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() - timedelta(minutes=5),
        last_seen_at=timezone.now() - timedelta(minutes=5),
    )

    _client, response = _signup_for_visitor(visitor_cookie)

    assert response.status_code == 200
    event = PublicAnalyticsEvent.objects.get(event_type="signup_started")
    assert event.session_id == valid.pk
    assert event.session_id not in {bot.pk, internal.pk}


def _make_user(email=None, **kwargs):
    email = email or f"signup-{uuid.uuid4().hex}@example.com"
    return get_user_model().objects.create_user(
        username=email,
        email=email,
        password="Valid-password-123!",
        **kwargs,
    )


def _completed_request(rf, visitor_cookie):
    request = rf.post("/accounts/signup/")
    request.COOKIES["eg_visitor_id"] = visitor_cookie
    return request


def _invoke_signup_completed(rf, visitor_cookie, user, capture_callbacks):
    with capture_callbacks(execute=True):
        return record_signup_completed_from_request(
            _completed_request(rf, visitor_cookie), user, "CL"
        )


def test_signup_completed_creates_event_and_links_same_first_touch_session(
    rf, django_capture_on_commit_callbacks
):
    visitor_cookie = uuid.uuid4().hex
    session = _make_attributed_session(visitor_cookie)
    user = _make_user()

    _invoke_signup_completed(rf, visitor_cookie, user, django_capture_on_commit_callbacks)

    assert user.pk is not None
    event = PublicAnalyticsEvent.objects.get(event_type="signup_completed")
    embudo = RegistroEmbudoSuscriptor.objects.get(user=user)
    assert event.session_id == session.pk
    assert embudo.public_session_id == session.pk
    assert event.metadata == {"source": "backend"}
    assert not hasattr(embudo, "utm_source")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SECURE_SSL_REDIRECT=False,
)
def test_successful_custom_signup_creates_completed_event_after_user_persistence(
    client, django_capture_on_commit_callbacks
):
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            "/cl/es/accounts/signup/?rubro=DESARMADURIA",
            {
                "email": "phase7a-success@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "first_name": "Mauricio",
                "nombre_taller": "Taller Phase 7A",
                "telefono": "+56911112222",
                "country": "CL",
                "rubro_principal_signup": "DESARMADURIA",
                "rubros_adicionales": [],
            },
        )

    user = get_user_model().objects.get(email="phase7a-success@example.com")
    event = PublicAnalyticsEvent.objects.get(event_type="signup_completed")
    embudo = RegistroEmbudoSuscriptor.objects.get(user=user)
    assert response.status_code == 200
    assert user.pk is not None
    assert event.session_id == embudo.public_session_id
    assert event.dedupe_key == "signup_completed"
    assert event.metadata == {"source": "backend"}


def test_signup_completed_is_idempotent_for_repeated_callbacks(
    rf, django_capture_on_commit_callbacks
):
    visitor_cookie = uuid.uuid4().hex
    session = _make_attributed_session(visitor_cookie)
    user = _make_user()
    request = _completed_request(rf, visitor_cookie)

    with django_capture_on_commit_callbacks(execute=True):
        record_signup_completed_from_request(request, user, "CL")
    with django_capture_on_commit_callbacks(execute=True):
        record_signup_completed_from_request(request, user, "CL")

    assert PublicAnalyticsEvent.objects.filter(event_type="signup_completed").count() == 1
    assert RegistroEmbudoSuscriptor.objects.filter(user=user).count() == 1
    assert RegistroEmbudoSuscriptor.objects.get(user=user).public_session_id == session.pk


def test_signup_completed_keeps_oldest_first_touch_across_session_rollover(
    rf, django_capture_on_commit_callbacks
):
    visitor_cookie = uuid.uuid4().hex
    oldest = _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() - timedelta(minutes=10),
        last_seen_at=timezone.now() - timedelta(minutes=10),
    )
    newer = _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() - timedelta(minutes=5),
        last_seen_at=timezone.now() - timedelta(minutes=5),
    )
    user = _make_user()

    _invoke_signup_completed(rf, visitor_cookie, user, django_capture_on_commit_callbacks)

    event = PublicAnalyticsEvent.objects.get(event_type="signup_completed")
    embudo = RegistroEmbudoSuscriptor.objects.get(user=user)
    assert event.session_id == oldest.pk
    assert embudo.public_session_id == oldest.pk
    assert event.session_id != newer.pk


def test_signup_completed_filters_talleres_before_selecting_salvage(
    rf, django_capture_on_commit_callbacks
):
    visitor_cookie = uuid.uuid4().hex
    talleres = _make_attributed_session(
        visitor_cookie,
        first_path="/cl/talleres/",
        last_path="/cl/talleres/",
        landing_path="/cl/talleres/",
        vertical_key="workshop",
        first_seen_at=timezone.now() - timedelta(minutes=10),
        last_seen_at=timezone.now() - timedelta(minutes=10),
    )
    salvage = _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() - timedelta(minutes=5),
        last_seen_at=timezone.now() - timedelta(minutes=5),
    )
    user = _make_user()

    _invoke_signup_completed(rf, visitor_cookie, user, django_capture_on_commit_callbacks)

    event = PublicAnalyticsEvent.objects.get(event_type="signup_completed")
    assert event.session_id == salvage.pk
    assert event.session_id != talleres.pk
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_completed").count() == 1


def test_signup_completed_direct_access_or_blocked_cookie_creates_no_event(
    rf, django_capture_on_commit_callbacks
):
    user = _make_user()
    request = rf.post("/accounts/signup/")

    with django_capture_on_commit_callbacks(execute=True):
        record_signup_completed_from_request(request, user, "CL")

    assert PublicAnalyticsEvent.objects.filter(event_type="signup_completed").count() == 0
    assert RegistroEmbudoSuscriptor.objects.filter(user=user).count() == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"first_seen_at": timezone.now() - timedelta(days=31)},
        {"expires_at": timezone.now() - timedelta(days=1)},
        {"is_bot": True},
        {"is_internal": True},
        {"country": "us"},
        {"vertical_key": "workshop"},
    ],
)
def test_signup_completed_rejects_invalid_attribution(
    rf, overrides, django_capture_on_commit_callbacks
):
    visitor_cookie = uuid.uuid4().hex
    _make_attributed_session(visitor_cookie, **overrides)
    user = _make_user()

    _invoke_signup_completed(rf, visitor_cookie, user, django_capture_on_commit_callbacks)

    assert PublicAnalyticsEvent.objects.filter(event_type="signup_completed").count() == 0
    assert RegistroEmbudoSuscriptor.objects.filter(user=user).count() == 0


def test_signup_completed_does_not_overwrite_existing_public_session(
    rf, django_capture_on_commit_callbacks
):
    visitor_cookie = uuid.uuid4().hex
    original = _make_attributed_session(visitor_cookie)
    later = _make_attributed_session(
        visitor_cookie,
        first_seen_at=timezone.now() + timedelta(minutes=1),
        last_seen_at=timezone.now() + timedelta(minutes=1),
    )
    user = _make_user()
    embudo = registrar_signup(user, "CL", public_session=later)

    _invoke_signup_completed(rf, visitor_cookie, user, django_capture_on_commit_callbacks)

    assert embudo.public_session_id == later.pk
    assert RegistroEmbudoSuscriptor.objects.get(user=user).public_session_id == later.pk
    event = PublicAnalyticsEvent.objects.get(event_type="signup_completed")
    assert event.session_id == later.pk
    assert event.session_id != original.pk


def test_signup_completed_rollback_does_not_create_event_or_embudo(rf):
    visitor_cookie = uuid.uuid4().hex
    _make_attributed_session(visitor_cookie)

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            user = _make_user()
            record_signup_completed_from_request(
                _completed_request(rf, visitor_cookie), user, "CL"
            )
            raise RuntimeError("rollback signup")

    assert get_user_model().objects.filter(email=user.email).count() == 0
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_completed").count() == 0
    assert RegistroEmbudoSuscriptor.objects.count() == 0


def test_signup_completed_analytics_failure_does_not_raise_or_remove_user(
    rf, django_capture_on_commit_callbacks
):
    visitor_cookie = uuid.uuid4().hex
    _make_attributed_session(visitor_cookie)
    user = _make_user()

    with patch(
        "taller.services.public_event_tracking.record_public_event",
        side_effect=RuntimeError("analytics unavailable"),
    ):
        _invoke_signup_completed(rf, visitor_cookie, user, django_capture_on_commit_callbacks)

    assert get_user_model().objects.filter(pk=user.pk).exists()
    assert RegistroEmbudoSuscriptor.objects.filter(user=user).exists()
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_completed").count() == 0


def test_signup_completed_never_creates_later_funnel_events(
    rf, django_capture_on_commit_callbacks
):
    visitor_cookie = uuid.uuid4().hex
    _make_attributed_session(visitor_cookie)
    user = _make_user()

    _invoke_signup_completed(rf, visitor_cookie, user, django_capture_on_commit_callbacks)

    assert PublicAnalyticsEvent.objects.filter(
        event_type__in={"company_created", "first_login"}
    ).count() == 0


def _invoke_company_created(user, capture_callbacks):
    with capture_callbacks(execute=True):
        return record_company_created_for_user(user)


def test_company_created_requires_persisted_empresa_and_uses_embudo_session(
    django_capture_on_commit_callbacks,
):
    visitor_cookie = uuid.uuid4().hex
    session = _make_attributed_session(visitor_cookie)
    user = _make_user()
    embudo = registrar_signup(user, "CL", public_session=session)
    empresa = EmpresaFactory(user=user, pais="CL")

    with django_capture_on_commit_callbacks(execute=True):
        registrar_empresa_creada(user)

    event = PublicAnalyticsEvent.objects.get(event_type="company_created")
    embudo.refresh_from_db()
    assert empresa.pk is not None
    assert embudo.empresa_creada_at is not None
    assert embudo.public_session_id == session.pk
    assert event.session_id == embudo.public_session_id
    assert event.dedupe_key == "company_created"
    assert event.metadata == {"source": "backend"}


def test_company_created_is_idempotent_for_callbacks_empresa_and_config_saves(
    django_capture_on_commit_callbacks,
):
    visitor_cookie = uuid.uuid4().hex
    session = _make_attributed_session(visitor_cookie)
    user = _make_user()
    registrar_signup(user, "CL", public_session=session)
    empresa = EmpresaFactory(user=user, pais="CL")
    config = ConfiguracionEmpresa.objects.create(empresa=empresa)

    with django_capture_on_commit_callbacks(execute=True):
        registrar_empresa_creada(user)
        registrar_empresa_creada(user)
        empresa.nombre_taller = "Nombre actualizado"
        empresa.save(update_fields=["nombre_taller"])
        config.rubro_principal = "DESARMADURIA"
        config.save(update_fields=["rubro_principal"])
        registrar_empresa_creada(user)

    assert PublicAnalyticsEvent.objects.filter(event_type="company_created").count() == 1
    assert RegistroEmbudoSuscriptor.objects.filter(user=user).count() == 1


def test_company_created_requires_embudo_and_public_session():
    user_without_embudo = _make_user()
    EmpresaFactory(user=user_without_embudo, pais="CL")
    registrar_empresa_creada(user_without_embudo)

    user_without_session = _make_user()
    registrar_signup(user_without_session, "CL")
    EmpresaFactory(user=user_without_session, pais="CL")
    registrar_empresa_creada(user_without_session)

    assert PublicAnalyticsEvent.objects.filter(event_type="company_created").count() == 0


def test_company_created_preserves_existing_embudo_attribution(
    django_capture_on_commit_callbacks,
):
    first_session = _make_attributed_session(uuid.uuid4().hex)
    second_session = _make_attributed_session(uuid.uuid4().hex)
    user = _make_user()
    embudo = registrar_signup(user, "CL", public_session=first_session)
    registrar_signup(user, "CL", public_session=second_session)
    EmpresaFactory(user=user, pais="CL")

    with django_capture_on_commit_callbacks(execute=True):
        registrar_empresa_creada(user)

    embudo.refresh_from_db()
    event = PublicAnalyticsEvent.objects.get(event_type="company_created")
    assert embudo.public_session_id == first_session.pk
    assert event.session_id == first_session.pk
    assert event.session_id != second_session.pk


@pytest.mark.parametrize("session_flags", [{"is_bot": True}, {"is_internal": True}])
def test_company_created_rejects_bot_or_internal_embudo_session(
    session_flags, django_capture_on_commit_callbacks
):
    session = _make_attributed_session(uuid.uuid4().hex, **session_flags)
    user = _make_user()
    registrar_signup(user, "CL", public_session=session)
    EmpresaFactory(user=user, pais="CL")

    with django_capture_on_commit_callbacks(execute=True):
        registrar_empresa_creada(user)

    assert PublicAnalyticsEvent.objects.filter(event_type="company_created").count() == 0


def test_company_created_rollback_does_not_emit_event():
    visitor_cookie = uuid.uuid4().hex
    session = _make_attributed_session(visitor_cookie)
    user = _make_user()
    registrar_signup(user, "CL", public_session=session)

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            EmpresaFactory(user=user, pais="CL")
            registrar_empresa_creada(user)
            raise RuntimeError("rollback empresa")

    assert not Empresa.objects.filter(user=user).exists()
    assert PublicAnalyticsEvent.objects.filter(event_type="company_created").count() == 0


def test_company_created_analytics_failure_does_not_remove_empresa(
    django_capture_on_commit_callbacks,
):
    session = _make_attributed_session(uuid.uuid4().hex)
    user = _make_user()
    registrar_signup(user, "CL", public_session=session)
    empresa = EmpresaFactory(user=user, pais="CL")

    with patch(
        "taller.services.public_event_tracking.record_public_event",
        side_effect=RuntimeError("analytics unavailable"),
    ):
        with django_capture_on_commit_callbacks(execute=True):
            registrar_empresa_creada(user)

    assert empresa.pk is not None
    assert PublicAnalyticsEvent.objects.filter(event_type="company_created").count() == 0


def test_company_created_reconciles_empresa_created_before_embudo(
    django_capture_on_commit_callbacks,
):
    session = _make_attributed_session(uuid.uuid4().hex)
    user = _make_user()
    EmpresaFactory(user=user, pais="CL")

    registrar_empresa_creada(user)
    assert PublicAnalyticsEvent.objects.filter(event_type="company_created").count() == 0

    with django_capture_on_commit_callbacks(execute=True):
        embudo = registrar_signup(user, "CL", public_session=session)

    event = PublicAnalyticsEvent.objects.get(event_type="company_created")
    embudo.refresh_from_db()
    assert embudo.empresa_creada_at is not None
    assert embudo.public_session_id == session.pk
    assert event.session_id == session.pk


def _login_request(rf, user, **attrs):
    request = rf.get("/cl/es/accounts/login/")
    request.user = user
    request.session = {}
    for name, value in attrs.items():
        setattr(request, name, value)
    return request


def test_first_login_uses_existing_embudo_session_and_persists_timestamp(
    rf, django_capture_on_commit_callbacks
):
    session = _make_attributed_session(uuid.uuid4().hex)
    user = _make_user()
    embudo = registrar_signup(user, "CL", public_session=session)

    from taller.reportes.services.registro_embudo_service import registrar_primer_login

    with django_capture_on_commit_callbacks(execute=True):
        registrar_primer_login(user, _login_request(rf, user))

    embudo.refresh_from_db()
    event = PublicAnalyticsEvent.objects.get(event_type="first_login")
    assert embudo.primer_login_at is not None
    assert event.session_id == embudo.public_session_id == session.pk
    assert event.metadata == {"source": "backend"}
    assert set(event.metadata) == {"source"}


def test_reportes_first_login_wrapper_delegates_to_canonical_once(rf):
    user = _make_user()
    request = _login_request(rf, user)

    with patch(
        "taller.services.registro_embudo_service.registrar_primer_login"
    ) as canonical:
        from taller.reportes.services.registro_embudo_service import registrar_primer_login

        registrar_primer_login(user, request=request)

    canonical.assert_called_once_with(user, request=request)


def test_active_login_receiver_reaches_canonical_once(rf):
    user = _make_user()
    request = _login_request(rf, user)

    with patch(
        "taller.services.registro_embudo_service.registrar_primer_login"
    ) as canonical:
        from taller.signals.pago_signals import registrar_primer_login_embudo

        registrar_primer_login_embudo(sender=user.__class__, request=request, user=user)

    canonical.assert_called_once_with(user, request=request)


@pytest.mark.parametrize("configured_domain", ["egarage.test", "@egarage.test"])
def test_configured_qa_domain_excludes_normalized_domain(rf, configured_domain):
    user = _make_user(email="qa-user@egarage.test")
    request = _login_request(rf, user)

    with override_settings(PUBLIC_ANALYTICS_QA_EMAIL_DOMAIN=configured_domain):
        assert is_internal_first_login_request(user, request) is True


def test_configured_qa_email_domain_normalizes_case_and_spaces(rf):
    user = _make_user(email="qa-user@egarage.test")
    request = _login_request(rf, user)

    with override_settings(PUBLIC_ANALYTICS_QA_EMAIL_DOMAIN="  @EGARAGE.TEST  "):
        assert is_internal_first_login_request(user, request) is True


def test_similar_domain_is_not_excluded_by_configured_qa_domain(rf):
    user = _make_user(email="user@noegarage.test.example")
    request = _login_request(rf, user)

    with override_settings(PUBLIC_ANALYTICS_QA_EMAIL_DOMAIN="egarage.test"):
        assert is_internal_first_login_request(user, request) is False


def test_empty_configured_qa_domain_does_not_exclude_by_email(rf):
    user = _make_user(email="user@egarage.test")
    request = _login_request(rf, user)

    with override_settings(PUBLIC_ANALYTICS_QA_EMAIL_DOMAIN=""):
        assert is_internal_first_login_request(user, request) is False


def test_impersonation_markers_are_preventive_only(rf):
    user = _make_user()
    request = _login_request(rf, user, is_impersonating=True)

    assert is_internal_first_login_request(user, request) is True
    assert not hasattr(request, "real_impersonation")


def test_first_login_repeated_signal_and_logout_login_is_idempotent(
    rf, django_capture_on_commit_callbacks
):
    session = _make_attributed_session(uuid.uuid4().hex)
    user = _make_user()
    registrar_signup(user, "CL", public_session=session)
    request = _login_request(rf, user)

    with django_capture_on_commit_callbacks(execute=True):
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        user_logged_in.send(sender=user.__class__, request=request, user=user)

    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 1
    assert PublicAnalyticsEvent.objects.filter(
        event_type__in={"signup_completed", "company_created"}
    ).count() == 0


def test_first_login_without_embudo_or_public_session_keeps_normal_login(rf):
    user = _make_user()
    from taller.reportes.services.registro_embudo_service import registrar_primer_login

    registrar_primer_login(user, _login_request(rf, user))
    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 0

    session = _make_attributed_session(uuid.uuid4().hex)
    user_with_unattributed_embudo = _make_user()
    registrar_signup(user_with_unattributed_embudo, "CL")
    registrar_primer_login(
        user_with_unattributed_embudo,
        _login_request(rf, user_with_unattributed_embudo),
    )
    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 0
    assert session.pk is not None


@pytest.mark.parametrize(
    "user_kwargs, request_attrs",
    [
        ({"is_staff": True}, {}),
        ({"is_superuser": True, "is_staff": True}, {}),
        ({"email": "qa@egarage.test"}, {}),
        ({}, {"COOKIES": {"eg_internal_traffic": "1"}}),
        ({}, {"qa_control_context": {"rubro": "DESARMADURIA"}}),
        ({}, {"session": {"qa_control": {"rubro": "DESARMADURIA"}}}),
        ({}, {"is_impersonating": True}),
    ],
)
def test_first_login_excludes_internal_staff_superuser_qa_and_impersonation(
    rf, user_kwargs, request_attrs
):
    session = _make_attributed_session(uuid.uuid4().hex)
    user = _make_user(**user_kwargs)
    registrar_signup(user, "CL", public_session=session)
    request = _login_request(rf, user)
    for name, value in request_attrs.items():
        setattr(request, name, value)

    from taller.reportes.services.registro_embudo_service import registrar_primer_login

    registrar_primer_login(user, request)

    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 0
    user.embudo_registro.refresh_from_db()
    assert user.embudo_registro.primer_login_at is None


@pytest.mark.parametrize(
    "session_overrides",
    [
        {"is_bot": True},
        {"is_internal": True},
        {"country": "us"},
        {"vertical_key": "workshop"},
        {"landing_path": "/cl/talleres/", "first_path": "/cl/talleres/"},
        {"first_seen_at": timezone.now() - timedelta(days=31)},
    ],
)
def test_first_login_rejects_invalid_linked_public_sessions(rf, session_overrides):
    session = _make_attributed_session(uuid.uuid4().hex, **session_overrides)
    user = _make_user()
    registrar_signup(user, "CL", public_session=session)

    from taller.reportes.services.registro_embudo_service import registrar_primer_login

    registrar_primer_login(user, _login_request(rf, user))
    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 0


def test_first_login_accepts_linked_session_when_either_path_is_desarmaduria(
    rf, django_capture_on_commit_callbacks
):
    for overrides in (
        {"landing_path": "/cl/talleres/", "first_path": "/cl/desarmadurias/"},
        {"landing_path": "/cl/desarmadurias/", "first_path": "/cl/talleres/"},
    ):
        session = _make_attributed_session(uuid.uuid4().hex, **overrides)
        user = _make_user()
        registrar_signup(user, "CL", public_session=session)

        from taller.reportes.services.registro_embudo_service import registrar_primer_login

        with django_capture_on_commit_callbacks(execute=True):
            registrar_primer_login(user, _login_request(rf, user))

    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 2


def test_first_login_analytics_failure_does_not_block_authentication(
    rf, django_capture_on_commit_callbacks
):
    session = _make_attributed_session(uuid.uuid4().hex)
    user = _make_user()
    registrar_signup(user, "CL", public_session=session)

    with patch(
        "taller.services.public_event_tracking.record_public_event",
        side_effect=RuntimeError("analytics unavailable"),
    ):
        from taller.reportes.services.registro_embudo_service import registrar_primer_login

        with django_capture_on_commit_callbacks(execute=True):
            registrar_primer_login(user, _login_request(rf, user))

    user.embudo_registro.refresh_from_db()
    assert user.embudo_registro.primer_login_at is not None
    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 0


def test_first_login_rollback_does_not_emit_event(rf):
    session = _make_attributed_session(uuid.uuid4().hex)
    user = _make_user()

    from taller.reportes.services.registro_embudo_service import registrar_primer_login

    registrar_signup(user, "CL", public_session=session)
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            registrar_primer_login(user, _login_request(rf, user))
            raise RuntimeError("rollback login")

    user.embudo_registro.refresh_from_db()
    assert user.embudo_registro.primer_login_at is None
    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 0


def test_public_endpoint_rejects_first_login():
    client = _csrf_client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")
    response = _post_event(
        client,
        {
            "event_type": "first_login",
            "path": "/cl/desarmadurias/",
            "dedupe_key": "first_login",
            "metadata": {"source": "backend"},
        },
    )
    assert response.status_code == 400
    assert response.json()["error"] == "event_type_not_allowed"


def test_custom_signup_does_not_auto_login_and_first_login_is_signal_driven(
    client, django_capture_on_commit_callbacks
):
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            "/cl/es/accounts/signup/?rubro=DESARMADURIA",
            {
                "email": "phase7c-auto-login@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "first_name": "Mauricio",
                "nombre_taller": "Taller Phase 7C",
                "telefono": "+56911112222",
                "country": "CL",
                "rubro_principal_signup": "DESARMADURIA",
                "rubros_adicionales": [],
            },
        )

    user = get_user_model().objects.get(email="phase7c-auto-login@example.com")
    assert response.wsgi_request.user.is_authenticated is False
    assert PublicAnalyticsEvent.objects.filter(event_type="first_login").count() == 0
    assert user.pk is not None


def test_signup_started_created_after_desarmaduria_visit_on_valid_signup_get():
    client = Client()
    client.get("/cl/desarmadurias/?utm_source=google", HTTP_USER_AGENT="Mozilla/5.0")

    response = client.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Mozilla/5.0")

    assert response.status_code == 200
    event = PublicAnalyticsEvent.objects.get(event_type="signup_started")
    session = PublicAnalyticsSession.objects.get()
    assert event.session == session
    assert event.path == "/accounts/signup/"
    assert event.dedupe_key == "signup_started"
    assert event.metadata == {"source": "backend", "source_path": "/cl/desarmadurias/"}
    assert RegistroEmbudoSuscriptor.objects.count() == 0


def test_signup_started_is_idempotent_for_attributed_session():
    client = Client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    first = client.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Mozilla/5.0")
    second = client.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Mozilla/5.0")

    assert first.status_code == 200
    assert second.status_code == 200
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_started").count() == 1


def test_signup_started_uses_oldest_first_touch_after_session_rollover():
    client = Client()
    client.get(
        "/cl/desarmadurias/?utm_source=google&utm_campaign=first",
        HTTP_USER_AGENT="Mozilla/5.0",
    )
    first = PublicAnalyticsSession.objects.get(utm_campaign="first")
    old_time = timezone.now() - timedelta(minutes=31)
    PublicAnalyticsSession.objects.filter(pk=first.pk).update(last_seen_at=old_time)

    client.get(
        "/cl/desarmadurias/?utm_source=meta&utm_campaign=second",
        HTTP_USER_AGENT="Mozilla/5.0",
    )
    response = client.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Mozilla/5.0")

    assert response.status_code == 200
    event = PublicAnalyticsEvent.objects.get(event_type="signup_started")
    assert event.session_id == first.pk
    assert PublicAnalyticsSession.objects.count() == 2


def test_signup_started_not_created_for_direct_signup_or_other_rubro_visit():
    direct = Client()
    direct_response = direct.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Mozilla/5.0")

    other = Client()
    other.get("/cl/talleres/", HTTP_USER_AGENT="Mozilla/5.0")
    other_response = other.get("/accounts/signup/?rubro=TALLER_MECANICO", HTTP_USER_AGENT="Mozilla/5.0")

    assert direct_response.status_code == 200
    assert other_response.status_code == 200
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_started").count() == 0


def test_signup_started_not_created_on_failed_signup_post():
    client = Client()
    client.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")

    response = client.post("/accounts/signup/?rubro=DESARMADURIA", data={}, HTTP_USER_AGENT="Mozilla/5.0")

    assert response.status_code in (200, 400)
    assert PublicAnalyticsEvent.objects.filter(event_type="signup_started").count() == 0


def test_signup_started_not_created_for_bot_internal_expired_or_visitor_mismatch():
    bot = Client()
    bot.get("/cl/desarmadurias/", HTTP_USER_AGENT="Googlebot/2.1")
    bot.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Googlebot/2.1")

    internal = Client()
    internal.cookies["eg_internal_traffic"] = "1"
    internal.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")
    internal.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Mozilla/5.0")

    expired = Client()
    expired.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")
    expired_session = PublicAnalyticsSession.objects.filter(is_bot=False, is_internal=False).latest("id")
    PublicAnalyticsSession.objects.filter(pk=expired_session.pk).update(
        first_seen_at=timezone.now() - timedelta(days=31),
        expires_at=timezone.now() - timedelta(days=1),
    )
    expired.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Mozilla/5.0")

    mismatch = Client()
    landing = mismatch.get("/cl/desarmadurias/", HTTP_USER_AGENT="Mozilla/5.0")
    assert "eg_visitor_id" in landing.cookies
    mismatch.cookies["eg_visitor_id"] = "different-visitor"
    mismatch.get("/accounts/signup/?rubro=DESARMADURIA", HTTP_USER_AGENT="Mozilla/5.0")

    assert PublicAnalyticsEvent.objects.filter(event_type="signup_started").count() == 0
