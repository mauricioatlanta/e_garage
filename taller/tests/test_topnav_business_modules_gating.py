"""
Tests para el gating por rubro de la barra de navegación superior legacy en
templates/base.html.

Contexto: esa barra es un bloque de navegación separado y hardcodeado
(independiente del sidebar dinámico resuelto por WorkspaceService/
business_modules context processor). Solo el botón "Desarme" estaba
correctamente condicionado a `{% if 'desarme' in business_modules %}`;
"Repuestos", "Vehículos" y "Servicios" se mostraban a CUALQUIER usuario
autenticado sin importar su rubro — reportado para el rubro RECYCLING
(Atlanta Reciclajes), donde no corresponden en absoluto.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory


@pytest.fixture
def empresa_recycling(db):
    user = User.objects.create_user("topnav_recycling", "topnav_rec@example.com", "pass1234")
    empresa = EmpresaFactory(user=user, nombre_taller="Recycling TopNav", pais="CL")
    ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal="RECYCLING")
    return empresa


@pytest.fixture
def empresa_workshop(db):
    user = User.objects.create_user("topnav_workshop", "topnav_wk@example.com", "pass1234")
    empresa = EmpresaFactory(user=user, nombre_taller="Workshop TopNav", pais="CL")
    ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal="WORKSHOP")
    return empresa


@pytest.mark.django_db
def test_topnav_recycling_no_muestra_repuestos_vehiculos_servicios(empresa_recycling):
    client = Client()
    client.force_login(empresa_recycling.user)

    response = client.get("/cl/es/reciclaje/")

    assert response.status_code == 200
    content = response.content.decode()
    assert ">Repuestos<" not in content
    assert ">Vehículos<" not in content
    assert ">Servicios<" not in content


@pytest.mark.django_db
def test_topnav_workshop_sigue_mostrando_repuestos_vehiculos_servicios(empresa_workshop):
    """Regresión: el rubro WORKSHOP (el caso común) no debe perder estos
    botones al agregar el gating por rubro."""
    client = Client()
    client.force_login(empresa_workshop.user)

    response = client.get("/cl/es/centro-operaciones/")

    assert response.status_code == 200
    content = response.content.decode()
    assert ">Repuestos<" in content
    assert ">Vehículos<" in content
    assert ">Servicios<" in content


@pytest.mark.django_db
def test_topnav_recycling_boton_compras_va_al_panel_de_reciclaje(empresa_recycling):
    """El botón que para el resto de rubros dice "Documentos" y lleva al
    formulario genérico (sin autocompletado ni catálogo de chatarra) debe
    decir "Compras" y llevar directo al panel de reciclaje para RECYCLING."""
    client = Client()
    client.force_login(empresa_recycling.user)

    response = client.get("/cl/es/reciclaje/")

    assert response.status_code == 200
    content = response.content.decode()
    assert ">Compras<" in content
    assert "/cl/es/reciclaje/" in content
    assert ">Documentos<" not in content


@pytest.mark.django_db
def test_topnav_workshop_sigue_mostrando_boton_documentos(empresa_workshop):
    """Regresión: el rubro WORKSHOP no debe perder el botón "Documentos"
    apuntando al formulario genérico."""
    client = Client()
    client.force_login(empresa_workshop.user)

    response = client.get("/cl/es/centro-operaciones/")

    assert response.status_code == 200
    content = response.content.decode()
    assert ">Documentos<" in content
    assert ">Compras<" not in content


@pytest.mark.django_db
def test_topnav_recycling_boton_reportes_va_al_reporte_de_reciclaje(empresa_recycling):
    """El botón "Reportes" para el resto de rubros lleva a un hub de 13+
    tarjetas de taller mecánico (reportes por técnico, recordatorios de
    mantención, vehículos atendidos, agenda...) — ninguna aplica a
    RECYCLING. Debe llevar directo al reporte de fechas del panel de
    reciclaje."""
    client = Client()
    client.force_login(empresa_recycling.user)

    response = client.get("/cl/es/reciclaje/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "/cl/es/reciclaje/reportes/" in content
    assert "reportes/reportes_dashboard" not in content


@pytest.mark.django_db
def test_topnav_workshop_sigue_mostrando_hub_de_reportes_generico(empresa_workshop):
    """Regresión: el rubro WORKSHOP no debe perder el link al hub de
    reportes genérico."""
    client = Client()
    client.force_login(empresa_workshop.user)

    response = client.get("/cl/es/centro-operaciones/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "/cl/es/reportes/" in content
    assert "/cl/es/reciclaje/reportes/" not in content
