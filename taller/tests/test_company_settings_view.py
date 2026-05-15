from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.models.tecnico import Tecnico


User = get_user_model()


@pytest.fixture(autouse=True)
def _company_settings_view_settings(settings):
    settings.SECURE_SSL_REDIRECT = False


def _make_user_and_company(username="settings-user", country="CL"):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="pass12345",
    )
    empresa = Empresa.objects.create(
        user=user,
        nombre_taller=f"Taller {username}",
        pais=country,
        telefono="+56911112222",
        email=user.email,
    )
    return user, empresa


@pytest.mark.django_db
def test_settings_post_persists_company_fields_and_legacy_config(client):
    user, empresa = _make_user_and_company()
    client.force_login(user)

    response = client.post(
        "/cl/es/settings/",
        {
            "section": "theme",
            "company_name": "Garage Sur",
            "tagline": "Servicio rapido",
            "phone": "+56987654321",
            "email": "contacto@garagesur.cl",
            "website": "https://garagesur.cl",
            "address": "Av. Siempre Viva 123",
            "tax_id": "76.123.456-7",
            "business_license": "LIC-7788",
            "currency": "USD",
            "tax_rate": "12.50",
            "apply_tax_by_default": "on",
            "primary_color": "#112233",
            "secondary_color": "#445566",
            "separate_by_technician": "on",
        },
        follow=False,
    )

    assert response.status_code == 302

    company_settings = user.company_settings
    company_settings.refresh_from_db()
    empresa.refresh_from_db()
    config_empresa = ConfiguracionEmpresa.objects.get(empresa=empresa)

    assert company_settings.company_name == "Garage Sur"
    assert company_settings.tagline == "Servicio rapido"
    assert company_settings.phone == "+56987654321"
    assert company_settings.email == "contacto@garagesur.cl"
    assert company_settings.website == "https://garagesur.cl"
    assert company_settings.address == "Av. Siempre Viva 123"
    assert company_settings.tax_id == "76.123.456-7"
    assert company_settings.business_license == "LIC-7788"
    assert company_settings.currency == "USD"
    assert company_settings.tax_rate == Decimal("12.50")
    assert company_settings.apply_tax_by_default is True
    assert company_settings.primary_color == "#112233"
    assert company_settings.secondary_color == "#445566"
    assert company_settings.separate_by_technician is True

    assert empresa.nombre_taller == "Garage Sur"
    assert empresa.telefono == "+56987654321"
    assert empresa.email == "contacto@garagesur.cl"
    assert empresa.direccion == "Av. Siempre Viva 123"

    assert config_empresa.nombre_publico == "Garage Sur"
    assert config_empresa.tagline == "Servicio rapido"
    assert config_empresa.telefono == "+56987654321"
    assert config_empresa.email_contacto == "contacto@garagesur.cl"
    assert config_empresa.sitio_web == "https://garagesur.cl"
    assert config_empresa.direccion == "Av. Siempre Viva 123"
    assert config_empresa.moneda == "USD"
    assert config_empresa.tasa_impuesto == Decimal("12.50")
    assert config_empresa.sales_tax_rate == Decimal("12.50")
    assert config_empresa.aplicar_impuesto_por_defecto is True
    assert config_empresa.dividir_por_tecnico is True
    assert config_empresa.brand_color == "#112233"


@pytest.mark.django_db
def test_settings_can_create_technician_with_contact_fields(client):
    user, _empresa = _make_user_and_company(username="settings-tech")
    client.force_login(user)

    response = client.post(
        "/cl/es/settings/",
        {
            "crear_tecnico": "1",
            "nombre": "Pedro Perez",
            "telefono": "+56955554444",
            "direccion": "Calle Taller 456",
        },
        follow=False,
    )

    assert response.status_code == 302

    tecnico = Tecnico.objects.get(empresa=user.empresa, nombre="Pedro Perez")
    assert tecnico.telefono == "+56955554444"
    assert tecnico.direccion == "Calle Taller 456"
    assert tecnico.activo is True


@pytest.mark.django_db
def test_settings_can_toggle_technician_status(client):
    user, empresa = _make_user_and_company(username="settings-toggle")
    tecnico = Tecnico.objects.create(
        empresa=empresa,
        nombre="Mario Gomez",
        telefono="+56911110000",
        activo=True,
    )
    client.force_login(user)

    response = client.post(
        "/cl/es/settings/",
        {
            "toggle_tecnico": str(tecnico.id),
        },
        follow=False,
    )

    assert response.status_code == 302

    tecnico.refresh_from_db()
    assert tecnico.activo is False
