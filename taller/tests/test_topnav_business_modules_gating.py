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
