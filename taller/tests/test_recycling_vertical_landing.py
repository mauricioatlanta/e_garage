"""
Tests para la incorporación del rubro RECYCLING como vertical de marketing
de primera clase (Fase 358): landing pública /cl/reciclaje/, tarjeta en el
hub de Chile, y opción "Reciclaje" en el formulario público de signup.

Antes de esta fase, RECYCLING solo existía como rubro interno
(ConfiguracionEmpresa.RUBRO_CHOICES) sin landing de adquisición propia y sin
poder elegirse en el signup — un visitante nuevo no tenía forma de indicar
que su negocio es de reciclaje.
"""

import pytest
from django.contrib.auth.models import User

from taller.country.engine import URL_SLUG_TO_VERTICAL, get_landing_context
from taller.forms.custom_signup import SIGNUP_RUBRO_GROUPS, CustomSignupForm
from taller.models.configuracion import ConfiguracionEmpresa


def test_reciclaje_slug_mapea_a_vertical_recycling():
    assert URL_SLUG_TO_VERTICAL["reciclaje"] == "recycling"


def test_get_landing_context_recycling_chile():
    ctx = get_landing_context("cl", "recycling")
    assert ctx["rubro_key"] == "RECICLAJE"
    assert "Reciclaje" in ctx["hero_h1"] or "catalítico" in ctx["hero_h1"].lower()
    assert ctx["language"] == "es"


@pytest.mark.django_db
def test_landing_reciclaje_chile_responde_200(client):
    response = client.get("/cl/reciclaje/", follow=False)
    assert response.status_code == 200
    content = response.content.decode()
    assert "Reciclaje" in content
    assert "?rubro=RECICLAJE" in content


@pytest.mark.django_db
def test_hub_chile_muestra_tarjeta_reciclaje(client):
    response = client.get("/cl/", follow=False)
    assert response.status_code == 200
    content = response.content.decode()
    assert "/cl/reciclaje/" in content
    assert "Reciclaje" in content


@pytest.mark.django_db
def test_hub_mexico_no_muestra_tarjeta_reciclaje(client):
    """RECYCLING solo está wireado para Chile por ahora — otros países no
    deben mostrar un link roto a una landing que no existe para ellos."""
    response = client.get("/mx/", follow=False)
    assert response.status_code == 200
    content = response.content.decode()
    assert "/mx/reciclaje/" not in content


def test_reciclaje_esta_en_signup_rubro_groups():
    keys = {g["key"] for g in SIGNUP_RUBRO_GROUPS}
    assert "RECICLAJE" in keys
    grupo = next(g for g in SIGNUP_RUBRO_GROUPS if g["key"] == "RECICLAJE")
    assert grupo["rubros"] == ["RECYCLING"]


@pytest.mark.django_db
def test_signup_selecciona_reciclaje_resuelve_rubro_recycling():
    from taller.tests.factories import EmpresaFactory

    user = User.objects.create_user("signup_recycling", "signup_rec@example.com", "pass1234")
    empresa = EmpresaFactory(user=user, nombre_taller="Nuevo Reciclador", pais="CL")

    stub = type(
        "Stub",
        (),
        {
            "signup_lang": "es",
            "cleaned_data": {
                "rubro_principal_signup": "RECICLAJE",
                "rubros_adicionales": [],
            },
        },
    )()

    rubros = CustomSignupForm._build_rubros_list(stub)
    assert rubros[0] == "RECYCLING"

    config = ConfiguracionEmpresa.objects.create(
        empresa=empresa, rubro_principal=rubros[0], rubros=rubros
    )
    assert config.rubro_principal == "RECYCLING"
