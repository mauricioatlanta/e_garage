import pytest
from django.test import RequestFactory

from taller.desarme.views import lista_piezas
from taller.tests.factories import EmpresaFactory, PiezaDesarmeFactory, VehiculoDesarmeFactory


@pytest.mark.django_db
def test_lista_piezas_search_finds_exact_piece_code():
    empresa = EmpresaFactory(nombre_taller="Taller Busqueda", pais="CL", plan="paid")
    vehiculo = VehiculoDesarmeFactory(empresa=empresa, patente="ALTQA1", anio=2018)
    PiezaDesarmeFactory(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        codigo="ALT-002",
        nombre="Alternador",
    )
    PiezaDesarmeFactory(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        codigo="MOT-999",
        nombre="Motor completo",
    )

    request = RequestFactory().get("/cl/es/desarme/piezas/", {"q": "ALT-002"})
    request.user = empresa.user

    response = lista_piezas(request)

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "ALT-002" in html
    assert "MOT-999" not in html


@pytest.mark.django_db
def test_lista_piezas_partial_search_finds_exact_piece_code():
    empresa = EmpresaFactory(nombre_taller="Taller Busqueda Parcial", pais="CL", plan="paid")
    vehiculo = VehiculoDesarmeFactory(empresa=empresa, patente="ALTQA2", anio=2018)
    PiezaDesarmeFactory(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        codigo="ALT-002",
        nombre="Alternador",
    )

    request = RequestFactory().get(
        "/cl/es/desarme/piezas/",
        {"q": "ALT-002", "partial": "1"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.user = empresa.user

    response = lista_piezas(request)

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "ALT-002" in html
    assert "No hay resultados con los filtros aplicados" not in html
