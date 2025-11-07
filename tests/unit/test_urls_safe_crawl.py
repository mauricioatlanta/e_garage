import pytest
from django.urls import get_resolver
from django.test import Client

@pytest.mark.django_db
def test_urls_without_kwargs_do_not_500():
    c = Client()
    for (pattern, _) in get_resolver().reverse_dict.items():
        # saltar pattern no-string (funciones o view objs)
        if not isinstance(pattern, str):
            continue
        # solo rutas "limpias"
        if "<" in pattern or ">" in pattern or "(" in pattern:
            continue
        resp = c.get(pattern) if pattern.startswith("/") else c.get(f"/{pattern}")
        assert resp.status_code in (200, 301, 302, 401, 403, 404, 405)
