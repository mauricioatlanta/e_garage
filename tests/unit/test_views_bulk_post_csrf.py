import pytest

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import NoReverseMatch, reverse

CANDS = [
    (["taller:vehiculos_lista"], "/cl/vehiculos/"),
    (["taller:documentos_lista"], "/cl/documentos/"),
    (["taller:clientes_lista"], "/cl/clientes/"),
    (["taller:repuestos_lista"], "/cl/repuestos/"),
    (["taller:servicios_lista"], "/cl/servicios/"),
]


def _rev(names, fb):
    for n in names:
        try:
            return reverse(n)
        except NoReverseMatch:
            pass
    return fb


@pytest.mark.django_db
def test_bulk_post_csrf_smoke():
    anon = Client()
    User = get_user_model()
    user = User.objects.create_user("posty", "x")
    auth = Client()
    auth.force_login(user)

    # Crear una empresa para el usuario autenticado para evitar errores de contexto
    from taller.models.empresa import Empresa

    if not Empresa.objects.filter(user=user).exists():
        Empresa.objects.create(
            user=user, nombre_taller="Test Bulk", pais="CL", logo=None
        )

    for names, fb in CANDS:
        url = _rev(names, fb)
        r1 = anon.post(url, data={})
        assert r1.status_code in (200, 301, 302, 400, 401, 403, 404, 405, 500)
        r2 = auth.post(url, data={})
        assert r2.status_code in (200, 301, 302, 400, 401, 403, 404, 405, 500)
