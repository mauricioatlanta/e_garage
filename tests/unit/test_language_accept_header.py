import pytest

from django.test import Client


@pytest.mark.django_db
def test_accept_language_redirects_are_safe():
    c = Client(headers={"accept-language": "en-US,en;q=0.9"})
    r = c.get("/cl/")
    assert r.status_code in (200, 301, 302, 404)  # sin 500

    c = Client(headers={"accept-language": "es-CL,es;q=0.8"})
    r = c.get("/us/")
    assert r.status_code in (200, 301, 302, 404)
