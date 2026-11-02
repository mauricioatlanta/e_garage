import pytest

from django.contrib.auth.models import User
from django.core.management import call_command

from taller.servicios.catalog_bootstrap import ensure_company_services_catalog
from taller.servicios.models import Servicio, ServicioName


@pytest.fixture
def empresa_cl(db):
    from taller.tests.factories import EmpresaFactory

    user = User.objects.create_user(username="bootstrap-cl", password="pass")
    return EmpresaFactory(user=user, nombre_taller="EG Bootstrap CL", pais="CL")


@pytest.fixture
def empresa_us(db):
    from taller.tests.factories import EmpresaFactory

    user = User.objects.create_user(username="bootstrap-us", password="pass")
    return EmpresaFactory(user=user, nombre_taller="EG Bootstrap US", pais="US")


@pytest.mark.django_db
def test_bootstrap_explicito_crea_exactamente_diez_servicios(empresa_cl):
    created = ensure_company_services_catalog(empresa_cl, "CL")

    assert created == 10
    assert Servicio.objects.filter(empresa=empresa_cl, categoria__country="CL").count() == 10


@pytest.mark.django_db
def test_bootstrap_explicito_segunda_ejecucion_es_idempotente(empresa_cl):
    primera = ensure_company_services_catalog(empresa_cl, "CL")
    assert primera == 10

    segunda = ensure_company_services_catalog(empresa_cl, "CL")

    assert segunda == 0
    assert Servicio.objects.filter(empresa=empresa_cl, categoria__country="CL").count() == 10


@pytest.mark.django_db
def test_bootstrap_explicito_traducciones_cl_y_us_funcionan(empresa_cl, empresa_us):
    ensure_company_services_catalog(empresa_cl, "CL")
    ensure_company_services_catalog(empresa_us, "US")

    nombre_cl = ServicioName.objects.get(
        servicio__empresa=empresa_cl,
        servicio__codigo_interno="MAINT_OIL_SYNTH",
        language="es",
    )
    nombre_us = ServicioName.objects.get(
        servicio__empresa=empresa_us,
        servicio__codigo_interno="MAINT_OIL_SYNTH",
        language="en",
    )

    assert nombre_cl.label == "Cambio de Aceite Sintético"
    assert nombre_us.label == "Full Synthetic Oil Change"


@pytest.mark.django_db
def test_management_command_bootstrapea_empresa_de_forma_explicita(empresa_cl):
    call_command("bootstrap_servicios_empresa", str(empresa_cl.pk))

    assert Servicio.objects.filter(empresa=empresa_cl, categoria__country="CL").count() == 10
