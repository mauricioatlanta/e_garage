"""
Tests para el redirect de /workspace/ a /reciclaje/ para el rubro RECYCLING.

Contexto: el login de un tenant RECYCLING (Atlanta Reciclajes) caía en
/cl/es/workspace/ mostrando la marca y los KPIs de "eGarage Repuestos"
(Casa de Repuestos) — el rubro nunca tuvo un WorkspaceDef propio, ni un
sistema de KPIs para sus propios modelos (CompraReciclaje, Catalitico).
En vez de duplicar ese sistema de KPIs, /workspace/ redirige directo al
dashboard de reciclaje ya construido, que sí tiene KPIs, gráficas y
actividad reciente correctos.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory


@pytest.fixture
def empresa_recycling(db):
    user = User.objects.create_user("wsredirect_recycling", "wsredirect_rec@example.com", "pass1234")
    empresa = EmpresaFactory(user=user, nombre_taller="Recycling WS Redirect", pais="CL")
    ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal="RECYCLING")
    return empresa


@pytest.fixture
def empresa_workshop(db):
    user = User.objects.create_user("wsredirect_workshop", "wsredirect_wk@example.com", "pass1234")
    empresa = EmpresaFactory(user=user, nombre_taller="Workshop WS Redirect", pais="CL")
    ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal="WORKSHOP")
    return empresa


@pytest.mark.django_db
def test_workspace_recycling_redirige_al_panel_de_reciclaje(empresa_recycling):
    client = Client()
    client.force_login(empresa_recycling.user)

    response = client.get("/cl/es/workspace/")

    assert response.status_code == 302
    assert response.url == "/cl/es/reciclaje/"


@pytest.mark.django_db
def test_workspace_workshop_no_redirige(empresa_workshop):
    """Regresión: el rubro WORKSHOP (el caso común) debe seguir viendo el
    dashboard genérico normalmente, sin redirect."""
    client = Client()
    client.force_login(empresa_workshop.user)

    response = client.get("/cl/es/workspace/")

    assert response.status_code == 200
