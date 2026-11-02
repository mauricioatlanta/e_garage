"""
Tests de EmpresaDominioAdmin — operabilidad de incluir_www (Fase 344/345).

Contexto: Fase 343 agregó EmpresaDominio.incluir_www (default=True) pero no
lo expuso en ninguna interfaz operable — ningún staff/admin podía cambiarlo
salvo por ORM/shell directo, contradiciendo su propio help_text ("Desactivar
solo si el tenant no puede o no quiere..."). Fase 345 lo agrega como campo
editable del ModelAdmin. Estos tests fijan que:
  - incluir_www está entre los fields del admin y NO en readonly_fields;
  - cname_target sigue reflejando incluir_www correctamente (True/False);
  - proxy.egarage.cl no vuelve a aparecer como destino.
"""

import pytest
from django.contrib import admin as django_admin
from django.contrib.auth.models import User

from taller.models.empresa_dominio import EmpresaDominio


@pytest.fixture
def empresa(db):
    from taller.tests.factories import EmpresaFactory
    user = User.objects.create_user("dominio_admin_user", "dom-admin@test.com", "pass")
    return EmpresaFactory(user=user, nombre_taller="Taller Dominio Admin Test", pais="CL")


def _model_admin():
    model_admin = django_admin.site._registry.get(EmpresaDominio)
    assert model_admin is not None, "EmpresaDominio no está registrado en el admin"
    return model_admin


def test_incluir_www_no_es_readonly():
    model_admin = _model_admin()
    assert "incluir_www" not in model_admin.readonly_fields


def test_incluir_www_esta_entre_los_fields_del_fieldset():
    model_admin = _model_admin()
    campos = [
        campo
        for _titulo, seccion in model_admin.fieldsets
        for campo in seccion["fields"]
    ]
    assert "incluir_www" in campos


@pytest.mark.django_db
def test_cname_target_con_incluir_www_true(settings, empresa):
    settings.CUSTOM_DOMAIN_VPS_IP = "203.0.113.10"
    ed = EmpresaDominio.objects.create(
        empresa=empresa, dominio="admin-www.cl", incluir_www=True,
    )
    texto = _model_admin().cname_target(ed)

    assert "A" in texto
    assert "203.0.113.10" in texto
    assert "CNAME" in texto
    assert "www" in texto
    assert "admin-www.cl" in texto
    assert "proxy.egarage.cl" not in texto


@pytest.mark.django_db
def test_cname_target_con_incluir_www_false(settings, empresa):
    settings.CUSTOM_DOMAIN_VPS_IP = "203.0.113.10"
    ed = EmpresaDominio.objects.create(
        empresa=empresa, dominio="admin-nowww.cl", incluir_www=False,
    )
    texto = _model_admin().cname_target(ed)

    assert "A" in texto
    assert "203.0.113.10" in texto
    assert "CNAME www" not in texto
    assert "proxy.egarage.cl" not in texto
