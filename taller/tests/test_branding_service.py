"""
Tests para BrandingService.

Cubre:
  - Defaults cuando no hay empresa ni modelos relacionados.
  - Resolución de branding con Empresa sola (Layer 3).
  - Resolución con ConfiguracionEmpresa (Layer 2 > Layer 3).
  - Resolución con CompanySettings (Layer 1 > Layer 2 > Layer 3).
  - get_brand_for_request() via RequestFactory.
  - as_context() retrocompatible con templates legacy.
  - sync_to_legacy_models() propaga correctamente cada campo.
"""

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory

from taller.models.company_settings import CompanySettings
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.services.branding_service import BrandData, BrandingService


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def owner(db):
    return User.objects.create_user("brand_owner", "owner@example.com", "pass")


@pytest.fixture
def empresa(db, owner):
    return Empresa.objects.create(
        user=owner,
        nombre_taller="Taller Fixture",
        pais="CL",
        email="taller@example.com",
        telefono="+56911111111",
    )


@pytest.fixture
def config_empresa(db, empresa):
    return ConfiguracionEmpresa.objects.create(
        empresa=empresa,
        nombre_publico="Taller Config",
        tagline="Servicio de calidad",
        brand_color="#aabbcc",
        moneda="CLP",
        rubro_principal="TIRE",
        email_contacto="config@example.com",
        telefono="+56922222222",
    )


@pytest.fixture
def company_settings(db, empresa):
    # La señal auto-crea CompanySettings al crear Empresa; actualizamos ese registro.
    cs, _ = CompanySettings.objects.update_or_create(
        user=empresa.user,
        defaults=dict(
            company_name="Taller CS",
            tagline="Lo mejor",
            primary_color="#001122",
            secondary_color="#334455",
            currency="USD",
            phone="+56933333333",
            email="cs@example.com",
            address="Av. Principal 123",
            website="https://taller.com",
        ),
    )
    return cs


# ── Tests: defaults ───────────────────────────────────────────────────────────


def test_defaults_devuelven_egarage():
    brand = BrandingService._defaults()
    assert brand.name == "eGarage"
    assert brand.primary_color == "#0d6efd"
    assert brand.currency == "CLP"
    assert brand.rubro == "WORKSHOP"
    assert brand.secciones == {}


def test_get_brand_none_empresa_devuelve_defaults():
    brand = BrandingService.get_brand(None)
    assert brand.name == "eGarage"


# ── Tests: Layer 3 (Empresa) ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_layer3_empresa_nombre_y_pais(empresa, owner):
    # La señal auto-crea CompanySettings; lo eliminamos para aislar Layer 3.
    CompanySettings.objects.filter(user=owner).delete()
    brand = BrandingService.get_brand(empresa)
    assert brand.name == "Taller Fixture"
    assert brand.country == "cl"
    assert brand.email == "taller@example.com"
    assert brand.phone == "+56911111111"


# ── Tests: Layer 2 (ConfiguracionEmpresa) ────────────────────────────────────


@pytest.mark.django_db
def test_layer2_conf_sobreescribe_empresa(empresa, config_empresa, owner):
    CompanySettings.objects.filter(user=owner).delete()
    brand = BrandingService.get_brand(empresa)
    assert brand.name == "Taller Config"
    assert brand.tagline == "Servicio de calidad"
    assert brand.primary_color == "#aabbcc"
    assert brand.rubro == "TIRE"
    assert brand.email == "config@example.com"
    assert brand.phone == "+56922222222"


# ── Tests: Layer 1 (CompanySettings) ─────────────────────────────────────────


@pytest.mark.django_db
def test_layer1_company_settings_sobreescribe_todo(empresa, config_empresa, company_settings):
    brand = BrandingService.get_brand(empresa, user=empresa.user)
    assert brand.name == "Taller CS"
    assert brand.tagline == "Lo mejor"
    assert brand.primary_color == "#001122"
    assert brand.secondary_color == "#334455"
    assert brand.currency == "USD"
    assert brand.phone == "+56933333333"
    assert brand.email == "cs@example.com"
    assert brand.address == "Av. Principal 123"
    assert brand.website == "https://taller.com"


@pytest.mark.django_db
def test_layer2_rubro_disponible_incluso_con_company_settings(empresa, config_empresa, company_settings):
    brand = BrandingService.get_brand(empresa, user=empresa.user)
    assert brand.rubro == "TIRE"


# ── Tests: as_context() ───────────────────────────────────────────────────────


def test_as_context_contiene_brand_y_aliases():
    brand = BrandData(name="Demo", primary_color="#ff0000", logo_url="/logo.png")
    ctx = BrandingService.as_context(brand)

    assert ctx["BRAND"]["name"] == "Demo"
    assert ctx["company_name"] == "Demo"
    assert ctx["company_logo_url"] == "/logo.png"
    assert ctx["primary_color"] == "#ff0000"
    assert ctx["company_color"] == "#ff0000"


# ── Tests: get_brand_for_request() ────────────────────────────────────────────


@pytest.mark.django_db
def test_get_brand_for_request_usuario_anonimo():
    rf = RequestFactory()
    req = rf.get("/cl/es/dashboard/")
    req.user = AnonymousUser()
    brand = BrandingService.get_brand_for_request(req)
    assert brand.name == "eGarage"


@pytest.mark.django_db
def test_get_brand_for_request_con_empresa_en_request(empresa, config_empresa):
    # Eliminar el CompanySettings auto-creado por señal para aislar Layer 2.
    CompanySettings.objects.filter(user=empresa.user).delete()
    rf = RequestFactory()
    req = rf.get("/cl/es/dashboard/")
    req.user = empresa.user
    req.empresa = empresa  # simula HostTenantMiddleware / EmpresaResolverMiddleware
    brand = BrandingService.get_brand_for_request(req)
    assert brand.name == "Taller Config"


# ── Tests: sync_to_legacy_models() ───────────────────────────────────────────


@pytest.mark.django_db
def test_sync_propaga_a_empresa_y_config(empresa, company_settings):
    config_empresa, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)

    BrandingService.sync_to_legacy_models(company_settings, config_empresa, empresa)

    empresa.refresh_from_db()
    config_empresa.refresh_from_db()

    assert empresa.nombre_taller == company_settings.company_name
    assert empresa.email == company_settings.email
    assert config_empresa.nombre_publico == company_settings.company_name
    assert config_empresa.tagline == company_settings.tagline
    assert config_empresa.brand_color == company_settings.primary_color
    assert config_empresa.moneda == company_settings.currency
    assert config_empresa.sitio_web == company_settings.website


@pytest.mark.django_db
def test_sync_no_sobreescribe_si_no_cambia(empresa, company_settings):
    """sync_to_legacy_models es idempotente: segunda llamada no hace save innecesario."""
    config_empresa, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)

    BrandingService.sync_to_legacy_models(company_settings, config_empresa, empresa)
    config_empresa.refresh_from_db()
    updated_at_before = config_empresa.actualizado_en if hasattr(config_empresa, "actualizado_en") else None

    BrandingService.sync_to_legacy_models(company_settings, config_empresa, empresa)
    config_empresa.refresh_from_db()
    updated_at_after = config_empresa.actualizado_en if hasattr(config_empresa, "actualizado_en") else None

    assert updated_at_before == updated_at_after


@pytest.mark.django_db
def test_sync_no_duplica_telefono_ya_usado(db, empresa, company_settings):
    from decimal import Decimal

    user2 = User.objects.create_user("owner2", "owner2@example.com", "pass")
    empresa2 = Empresa.objects.create(
        user=user2,
        nombre_taller="Taller 2",
        pais="CL",
        telefono=company_settings.phone,  # mismo teléfono → debe rechazarse
    )
    config_empresa, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)

    # No debe lanzar IntegrityError; simplemente omite el teléfono
    BrandingService.sync_to_legacy_models(company_settings, config_empresa, empresa)
    empresa.refresh_from_db()
    assert empresa.telefono != company_settings.phone  # no sobrescribió
