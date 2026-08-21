import pytest

from django.contrib.auth.models import User
from django.urls import reverse

from taller.servicios.models import CategoriaServicio, Servicio


@pytest.fixture
def empresa_a(db):
    from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory

    user = User.objects.create_user(username="crear-servicio-a", password="pass")
    empresa = EmpresaFactory(user=user, nombre_taller="EG Empresa A", pais="CL")
    ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal="TIRE")
    return empresa


@pytest.fixture
def empresa_b(db):
    from taller.tests.factories import EmpresaFactory

    user = User.objects.create_user(username="crear-servicio-b", password="pass")
    return EmpresaFactory(user=user, nombre_taller="EG Empresa B", pais="CL")


@pytest.fixture
def auth_client_a(client, empresa_a):
    client.force_login(empresa_a.user)
    return client


@pytest.fixture
def categoria_cl(db):
    return CategoriaServicio.objects.create(country="CL", code="MANT", activo=True)


@pytest.mark.django_db
def test_crear_servicio_manual_es_tenant_scoped(auth_client_a, empresa_a, empresa_b, categoria_cl):
    response = auth_client_a.post(
        reverse("chile:taller:servicios:crear_servicio"),
        {"nombre": "Rotacion de Neumaticos Manual", "categoria": categoria_cl.pk},
    )

    assert response.status_code in (302, 200)

    servicio = Servicio.objects.get(nombre="Rotacion de Neumaticos Manual")
    assert servicio.empresa_id == empresa_a.pk
    assert not Servicio.objects.filter(
        empresa=empresa_b, nombre="Rotacion de Neumaticos Manual"
    ).exists()


@pytest.mark.django_db
def test_crear_servicio_manual_duplicado_exacto_falla(auth_client_a, empresa_a, categoria_cl):
    Servicio.objects.create(
        empresa=empresa_a,
        nombre="Cambio de Aceite Manual",
        categoria=categoria_cl,
    )
    total_antes = Servicio.objects.filter(empresa=empresa_a).count()

    response = auth_client_a.post(
        reverse("chile:taller:servicios:crear_servicio"),
        {"nombre": "Cambio de Aceite Manual", "categoria": categoria_cl.pk},
    )

    assert response.status_code == 200
    assert "form" in response.context
    assert response.context["form"].errors
    assert Servicio.objects.filter(empresa=empresa_a).count() == total_antes
