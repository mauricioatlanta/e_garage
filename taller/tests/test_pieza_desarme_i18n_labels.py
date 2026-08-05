# -*- coding: utf-8 -*-
"""
Tests para nombres traducibles y por empresa en PiezaDesarme.
- get_display_label: prioridad company → catalog → nombre
- inventario_inteligente serializa nombre con idioma activo
- API api_pieza_label_empresa_guardar crea/actualiza label por empresa
"""
import json

import pytest
from django.contrib.auth.models import User

from taller.models.empresa import Empresa
from taller.models.pieza_desarme import (
    PiezaDesarme,
    PiezaDesarmeName,
    PiezaDesarmeCompanyLabel,
)
from taller.models.vehiculo_desarme import VehiculoDesarme


@pytest.fixture
def empresa_user(db):
    from taller.tests.factories import EmpresaFactory
    empresa = EmpresaFactory(nombre_taller="Taller i18n", pais="CL", plan="paid")
    return empresa, empresa.user


@pytest.fixture
def vehiculo_desarme(empresa_user):
    empresa, _ = empresa_user
    return VehiculoDesarme.objects.create(
        empresa=empresa,
        patente="DES999",
        anio=2020,
    )


@pytest.fixture
def pieza_sin_nombres(empresa_user, vehiculo_desarme):
    empresa, _ = empresa_user
    return PiezaDesarme.objects.create(
        empresa=empresa,
        vehiculo_desarme=vehiculo_desarme,
        codigo="MOT-01",
        nombre="Motor completo",
        cantidad=1,
        activo=True,
    )


@pytest.mark.django_db
class TestGetDisplayLabel:
    """get_display_label prioriza company label, luego catalog, luego self.nombre."""

    def test_sin_company_ni_catalog_usa_nombre(self, pieza_sin_nombres):
        pieza = pieza_sin_nombres
        empresa = pieza.empresa
        assert pieza.get_display_label(empresa=empresa, language="es") == "Motor completo"
        assert pieza.get_display_label(empresa=None, language="es") == "Motor completo"

    def test_con_catalog_label_sin_company(self, pieza_sin_nombres):
        pieza = pieza_sin_nombres
        PiezaDesarmeName.objects.create(
            pieza_desarme=pieza,
            language="es",
            label="Motor completo (catálogo)",
            is_default=True,
        )
        assert (
            pieza.get_display_label(empresa=pieza.empresa, language="es")
            == "Motor completo (catálogo)"
        )

    def test_company_label_prioridad(self, pieza_sin_nombres):
        pieza = pieza_sin_nombres
        PiezaDesarmeName.objects.create(
            pieza_desarme=pieza,
            language="es",
            label="Motor (catálogo)",
            is_default=True,
        )
        PiezaDesarmeCompanyLabel.objects.create(
            empresa=pieza.empresa,
            pieza_desarme=pieza,
            language="es",
            label="Mi motor preferido",
        )
        assert pieza.get_display_label(empresa=pieza.empresa, language="es") == "Mi motor preferido"

    def test_empresa_none_devuelve_catalog_o_nombre(self, pieza_sin_nombres):
        pieza = pieza_sin_nombres
        PiezaDesarmeCompanyLabel.objects.create(
            empresa=pieza.empresa,
            pieza_desarme=pieza,
            language="es",
            label="Solo empresa",
        )
        # Sin empresa no usa company label
        out = pieza.get_display_label(empresa=None, language="es")
        assert out == "Motor completo"


@pytest.mark.django_db
class TestInventarioInteligenteSerializaNombre:
    """inventario_inteligente serializa nombre traducido usando idioma activo."""

    def test_inventario_inteligente_usa_display_label(self, empresa_user, vehiculo_desarme):
        empresa, user = empresa_user
        pieza = PiezaDesarme.objects.create(
            empresa=empresa,
            vehiculo_desarme=vehiculo_desarme,
            codigo="VALVE-01",
            nombre="Tapa de válvulas",
            cantidad=1,
            activo=True,
        )
        PiezaDesarmeName.objects.create(
            pieza_desarme=pieza,
            language="en",
            label="Valve Cover",
            is_default=True,
        )
        # Llamar a la vista directamente para no depender del ROOT_URLCONF (puede no incluir desarme)
        from django.test import RequestFactory
        from taller.desarme.views_inventario import inventario_inteligente

        request = RequestFactory().get("/desarme/vehiculos/1/inventario-inteligente/")
        request.user = user
        request.LANGUAGE_CODE = "es"
        resp = inventario_inteligente(request, pk=vehiculo_desarme.pk)
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        # El template embebe el JSON via repuestos_json|escapejs; verificar el nombre visible
        assert "Tapa de válvulas" in content


@pytest.mark.django_db
class TestApiPiezaLabelEmpresaGuardar:
    """Endpoint POST api_pieza_label_empresa_guardar crea o actualiza label por empresa."""

    def test_crear_label_empresa(self, empresa_user, pieza_sin_nombres):
        empresa, user = empresa_user
        from django.test import RequestFactory
        from taller.desarme.views import api_pieza_label_empresa_guardar

        request = RequestFactory().post(
            "/api/piezas/1/label-empresa/",
            data=json.dumps(
                {"language": "en", "label": "Engine Assembly", "aliases": ["motor", "engine"]}
            ),
            content_type="application/json",
        )
        request.user = user
        resp = api_pieza_label_empresa_guardar(request, pk=pieza_sin_nombres.pk)
        assert resp.status_code == 200
        data = json.loads(resp.content.decode("utf-8"))
        assert data.get("success") is True
        assert data.get("label") == "Engine Assembly"
        assert data.get("language") == "en"
        assert "motor" in data.get("aliases", [])

        rec = PiezaDesarmeCompanyLabel.objects.get(
            empresa=empresa, pieza_desarme=pieza_sin_nombres, language="en"
        )
        assert rec.label == "Engine Assembly"

    def test_actualizar_label_empresa(self, empresa_user, pieza_sin_nombres):
        empresa, user = empresa_user
        PiezaDesarmeCompanyLabel.objects.create(
            empresa=empresa,
            pieza_desarme=pieza_sin_nombres,
            language="es",
            label="Nombre antiguo",
        )
        from django.test import RequestFactory
        from taller.desarme.views import api_pieza_label_empresa_guardar

        request = RequestFactory().post(
            "/api/piezas/1/label-empresa/",
            data=json.dumps({"language": "es", "label": "Nombre nuevo", "aliases": []}),
            content_type="application/json",
        )
        request.user = user
        resp = api_pieza_label_empresa_guardar(request, pk=pieza_sin_nombres.pk)
        assert resp.status_code == 200
        assert json.loads(resp.content.decode("utf-8")).get("label") == "Nombre nuevo"
        rec = PiezaDesarmeCompanyLabel.objects.get(
            empresa=empresa, pieza_desarme=pieza_sin_nombres, language="es"
        )
        assert rec.label == "Nombre nuevo"

    def test_solo_pieza_de_empresa(self, empresa_user, pieza_sin_nombres):
        _, user = empresa_user
        from taller.tests.factories import EmpresaFactory
        otra_empresa = EmpresaFactory(nombre_taller="Otra", pais="CL", plan="paid")
        from django.test import RequestFactory
        from taller.desarme.views import api_pieza_label_empresa_guardar

        otro_veh = VehiculoDesarme.objects.create(
            empresa=otra_empresa,
            patente="OTRO",
            anio=2020,
        )
        otra_pieza = PiezaDesarme.objects.create(
            empresa=otra_empresa,
            vehiculo_desarme=otro_veh,
            codigo="X",
            nombre="Otra",
            cantidad=1,
            activo=True,
        )
        request = RequestFactory().post(
            "/api/piezas/1/label-empresa/",
            data=json.dumps({"language": "es", "label": "Hack", "aliases": []}),
            content_type="application/json",
        )
        request.user = user
        from django.http import Http404
        with pytest.raises(Http404):
            api_pieza_label_empresa_guardar(request, pk=otra_pieza.pk)
