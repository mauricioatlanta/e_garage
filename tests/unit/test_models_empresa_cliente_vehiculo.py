import pytest


@pytest.mark.django_db
def test_empresa_cliente_vehiculo_minimal_creation():
    # Importa las clases reales (Cliente está en 'clientes.py')
    from importlib import import_module

    Empresa = import_module("taller.models.empresa").Empresa
    Cliente = import_module("taller.models.clientes").Cliente
    Vehiculo = import_module("taller.models.vehiculos").Vehiculo

    # Empresa mínima - necesita un User primero
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="testuser", email="test@example.com")

    try:
        emp = Empresa.objects.create(
            user=user, nombre_taller="Acme Taller", empresa="Acme Corp", pais="CL"
        )
    except TypeError:
        # Si tu Empresa pide otros campos obligatorios sin default, agrega aquí
        emp = Empresa.objects.create(user=user, nombre_taller="Acme Taller")

    # Cliente mínimo
    cli_kwargs = {"empresa": emp, "nombre": "Juan"}
    for k in ("rut", "ein", "identificacion"):
        if k in {f.name for f in Cliente._meta.fields}:
            cli_kwargs[k] = "1-9"
            break
    cli = Cliente.objects.create(**cli_kwargs)

    # Vehículo mínimo (ajusta si tus campos difieren)
    v_kwargs = {
        "empresa": emp,
        "cliente": cli,
        "patente": "ABCZ12",
        "marca_texto": "Toyota",
        "modelo_texto": "Yaris",
        "anio": 2018,
    }

    v = Vehiculo.objects.create(**v_kwargs)

    # Relaciones y __str__
    assert v.empresa_id == emp.id and v.cliente_id == cli.id
    assert str(emp) and str(cli) and str(v)
