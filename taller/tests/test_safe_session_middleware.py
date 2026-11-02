import pytest
from django.conf import settings
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.test import override_settings
from django.urls import path


def concurrent_session_delete_view(request):
    request.session.get("country")
    Session.objects.filter(session_key=request.session.session_key).delete()
    return HttpResponse("ok")


urlpatterns = [
    path("", concurrent_session_delete_view, name="concurrent_session_delete"),
]


@pytest.mark.django_db
@override_settings(ROOT_URLCONF=__name__, SESSION_SAVE_EVERY_REQUEST=True)
def test_concurrent_session_delete_does_not_raise_sessioninterrupted(client):
    session = client.session
    session["country"] = "cl"
    session.save()

    response = client.get("/")

    assert response.status_code == 200
    assert response.content == b"ok"
    assert settings.SESSION_COOKIE_NAME in response.cookies
    assert response.cookies[settings.SESSION_COOKIE_NAME].value == ""

def test_active_settings_use_safe_session_middleware():
    import gestion_taller.settings as app_settings

    assert "taller.middleware.safe_session.SafeSessionMiddleware" in app_settings.MIDDLEWARE
    assert "django.contrib.sessions.middleware.SessionMiddleware" not in app_settings.MIDDLEWARE


def test_compacto_settings_use_safe_session_middleware():
    import gestion_taller.compacto.settings as compacto_settings

    assert "taller.middleware.safe_session.SafeSessionMiddleware" in compacto_settings.MIDDLEWARE
    assert "django.contrib.sessions.middleware.SessionMiddleware" not in compacto_settings.MIDDLEWARE
