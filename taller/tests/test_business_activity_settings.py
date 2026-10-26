import pytest
from django.contrib.auth.models import Group, User

from taller.forms.configuracion_forms import ConfiguracionServiciosForm
from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory


@pytest.mark.django_db
def test_activity_form_replaces_old_selection_and_normalizes_primary_first():
    config = ConfiguracionEmpresaFactory(
        rubro_principal="PARTS",
        rubros=["PARTS", "TIRE"],
    )
    form = ConfiguracionServiciosForm(
        data={
            "actividad_principal": "DESARMADURIA",
            "actividades_adicionales": ["TALLER_MECANICO", "DESARMADURIA"],
        },
        instance=config,
    )
    assert form.is_valid(), form.errors
    saved = form.save()
    assert saved.rubro_principal == "DESARMADURIA"
    assert saved.rubros == ["DESARMADURIA", "WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY"]
    assert "PARTS" not in saved.rubros


@pytest.mark.django_db
def test_activity_form_rejects_invalid_codes():
    config = ConfiguracionEmpresaFactory()
    form = ConfiguracionServiciosForm(
        data={"actividad_principal": "INVALID", "actividades_adicionales": []},
        instance=config,
    )
    assert not form.is_valid()


@pytest.mark.django_db
def test_activity_settings_rejects_non_privileged_user(client):
    owner = User.objects.create_user("owner-activities", password="x")
    empresa = EmpresaFactory(user=owner, with_config=False)
    ConfiguracionEmpresaFactory(empresa=empresa)
    vendedor = User.objects.create_user("seller-activities", password="x")
    Group.objects.get_or_create(name="Vendedor")[0].user_set.add(vendedor)
    from taller.models import TeamMember
    TeamMember.objects.create(user=vendedor, empresa=empresa, rol="Vendedor", is_active=True)

    client.force_login(vendedor)
    response = client.get("/cl/es/settings/activities/")
    assert response.status_code == 403
