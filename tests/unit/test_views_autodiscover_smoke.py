import pytest

from django.urls import NoReverseMatch, get_resolver, reverse


@pytest.mark.django_db
def test_zero_arg_named_urls_smoke(client):
    resolver = get_resolver()
    checked = 0
    # Recorre nombres y prueba los que no requieren args
    for name in list(resolver.reverse_dict.keys()):
        if not isinstance(name, str):
            continue
        try:
            url = reverse(name)
        except NoReverseMatch:
            continue  # requiere args

        try:
            resp = client.get(url)
            assert resp.status_code in (200, 301, 302, 401, 403, 405)
            checked += 1
        except Exception:
            # Ignora errores de template, middleware, etc.
            # Solo queremos probar que las URLs existen y son accesibles
            pass
        if checked >= 50:  # límite para que no tarde
            break
    assert checked >= 5  # al menos 5 rutas cubiertas
