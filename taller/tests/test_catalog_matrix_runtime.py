import pytest
from django.contrib.auth.models import User

from taller.models import ConfiguracionEmpresa, Empresa
from taller.servicios.catalog_bootstrap import (
    choose_country_translation,
    load_service_catalog_matrix,
    normalize_company_rubros,
    select_applicable_catalog_rows,
    sync_company_service_catalog,
)
from taller.servicios.models import (
    CategoriaServicio,
    Servicio,
    ServicioName,
    ServicioRubro,
)


pytestmark = pytest.mark.django_db


def _make_empresa(username, pais):
    user = User.objects.create_user(username=username, password="pass")
    return Empresa.objects.create(user=user, nombre_taller=username, pais=pais)


def test_runtime_catalog_contract():
    rows = load_service_catalog_matrix()

    assert len(rows) == 111
    assert len({row["candidate_code"] for row in rows}) == 111

    edges = {
        (row["candidate_code"], rubro)
        for row in rows
        for rubro in row["rubros"]
    }

    assert len(edges) == 711


def test_selector_workshop_y_parts():
    workshop = select_applicable_catalog_rows({"WORKSHOP"})
    parts = select_applicable_catalog_rows({"PARTS"})

    assert len(workshop) == 109
    assert len(parts) == 0


def test_country_translation_local_y_fallback():
    rows = load_service_catalog_matrix()

    direct_row = next(
        row
        for row in rows
        if row["candidate_code"] == "DIAGNOSTICO_COMPUTARIZADO_CON_ESCANER_OBD_II"
    )

    uy = choose_country_translation(direct_row, "UY")

    assert uy["country_code"] == "UY"
    assert uy["source"] == "UY"
    assert uy["label"]

    pending_row = next(
        row
        for row in rows
        if row["translations"]["UY"].get("status") == "pending"
    )

    fallback = choose_country_translation(pending_row, "UY")

    assert fallback["country_code"] == "CL"
    assert fallback["source"] == "CL_FALLBACK"
    assert fallback["label"] == pending_row["translations"]["CL"]["label"]


def test_normalize_company_rubros():
    empresa = _make_empresa("legacy-rubros", "CL")

    config = ConfiguracionEmpresa.objects.create(
        empresa=empresa,
        rubro_principal="WORKSHOP",
        rubros=["WORKSHOP", "DESARME", "REPUESTOS"],
    )

    assert normalize_company_rubros(config) == {"WORKSHOP", "DESARMADURIA", "PARTS"}


def test_sync_company_catalog_idempotent_and_multirubro():
    empresa = _make_empresa("workshop-matrix", "UY")

    ConfiguracionEmpresa.objects.create(
        empresa=empresa,
        rubro_principal="WORKSHOP",
        rubros=["WORKSHOP"],
    )

    first = sync_company_service_catalog(empresa, "UY")
    second = sync_company_service_catalog(empresa, "UY")

    assert first["selected"] == 109
    assert first["created"] == 109

    assert second["selected"] == 109
    assert second["created"] == 0

    assert Servicio.objects.filter(empresa=empresa).count() == 109

    service = Servicio.objects.filter(empresa=empresa).exclude(codigo_interno="").first()
    assert service is not None

    assert ServicioRubro.objects.filter(servicio=service).exists()
    assert ServicioName.objects.filter(
        servicio=service, country_code="CL", language="es"
    ).exists()


def test_sync_preserves_existing_price():
    empresa = _make_empresa("precio", "CL")

    ConfiguracionEmpresa.objects.create(
        empresa=empresa,
        rubro_principal="WORKSHOP",
        rubros=["WORKSHOP"],
    )

    sync_company_service_catalog(empresa, "CL")

    servicio = Servicio.objects.filter(empresa=empresa).exclude(codigo_interno="").first()

    servicio.precio_base = 12345
    servicio.save(update_fields=["precio_base"])

    sync_company_service_catalog(empresa, "CL")

    servicio.refresh_from_db()

    assert servicio.precio_base == 12345


def test_sync_does_not_touch_custom_service():
    empresa = _make_empresa("custom", "CL")

    ConfiguracionEmpresa.objects.create(
        empresa=empresa,
        rubro_principal="WORKSHOP",
        rubros=["WORKSHOP"],
    )

    categoria = CategoriaServicio.objects.create(
        country="CL",
        code="custom_test",
        activo=True,
    )

    custom = Servicio.objects.create(
        empresa=empresa,
        categoria=categoria,
        nombre="Servicio Personalizado",
        precio_base=777,
        activo=True,
        codigo_interno="",
    )

    sync_company_service_catalog(empresa, "CL")

    custom.refresh_from_db()

    assert custom.nombre == "Servicio Personalizado"
    assert custom.precio_base == 777
    assert custom.activo is True
