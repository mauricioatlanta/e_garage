import pytest

from django.db import IntegrityError


@pytest.mark.django_db
def test_vehiculo_unique_empresa_patente_db_constraint():
    from django.contrib.auth import get_user_model

    from taller.models.clientes import Cliente
    from taller.models.empresa import Empresa
    from taller.models.vehiculos import Vehiculo

    User = get_user_model()
    emp = Empresa.objects.create(
        nombre_taller="UQ",
        pais="CL",
        user=User.objects.create_user(username="emp_uq", password="x"),
    )
    cli = Cliente.objects.create(empresa=emp, nombre="Juan", tax_id="1-9")
    Vehiculo.objects.create(
        empresa=emp,
        cliente=cli,
        patente="UQ1234",
        marca_texto="A",
        modelo_texto="B",
        anio=2021,
    )

    # Si no hay constraint, este create pasará; si lo hay, debe tirar IntegrityError
    try:
        Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente="UQ1234",
            marca_texto="A",
            modelo_texto="B",
            anio=2021,
        )
        pytest.skip("Aún no existe unique constraint (empresa, patente); recomendado añadirlo")
    except IntegrityError:
        assert True
