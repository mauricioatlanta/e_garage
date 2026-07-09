"""
Fase 6.3a: regresión introducida por el corte de VehiculoDesarmeForm a
VehiculoDesarme (Fase 6.2) -- _guardar_danos_carroceria() hacía
InspeccionIngreso.objects.update_or_create(vehiculo=vehiculo, ...), pero
InspeccionIngreso.vehiculo es FK a Vehiculo (no nullable) y 'vehiculo' acá ya
es un VehiculoDesarme desde el corte. Reproduce el escenario exacto: alta de
vehículo de desarme con datos de daños de carrocería cargados (la sección
zona_N/tipo_dano_N/descripcion_N que el propio form expone).
"""

import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from taller.desarme.views import crear_vehiculo, editar_vehiculo
from taller.models.inspeccion_ingreso import InspeccionIngreso
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculo_desarme import VehiculoDesarme


@pytest.fixture
def user_logueado(empresa_chile):
    empresa_chile.user.empresa = empresa_chile
    return empresa_chile.user


@pytest.fixture
def marca_modelo(db):
    marca = Marca.objects.create(country="CL", nombre="MarcaDanosTest")
    modelo = Modelo.objects.create(country="CL", marca=marca, nombre="ModeloDanosTest")
    return marca, modelo


def _post(rf, path, user, data):
    request = rf.post(path, data=data)
    request.user = user
    request.session = SessionStore()
    request.session.create()
    request._messages = FallbackStorage(request)
    return request


def _datos_alta_con_danos(marca, modelo):
    return {
        "patente": "DANOTEST1",
        "vin": "",
        "marca": str(marca.pk),
        "modelo": str(modelo.pk),
        "anio": "2020",
        "motor": "",
        "caja": "",
        "color": "",
        "tipo_carroceria": "",
        "estado_desarme": "INGRESADO",
        # Sección de daños de carrocería que el form ya expone.
        "zona_0": "capo",
        "tipo_dano_0": "golpe",
        "descripcion_0": "Abolladura en el capó, prueba de regresión.",
    }


def test_alta_con_danos_carroceria_ya_no_revienta(db, empresa_chile, user_logueado, marca_modelo):
    """Antes del fix: ValueError, 'InspeccionIngreso.vehiculo' must be a
    'Vehiculo' instance, y la transacción completa de alta se revertía."""
    rf = RequestFactory()
    marca, modelo = marca_modelo
    request = _post(
        rf, "/cl/es/desarme/vehiculos/crear/", user_logueado, _datos_alta_con_danos(marca, modelo)
    )
    response = crear_vehiculo(request)

    assert response.status_code == 302, getattr(response, "content", b"").decode(
        "utf-8", errors="replace"
    )

    vehiculo = VehiculoDesarme.objects.get(empresa=empresa_chile, patente="DANOTEST1")
    inspeccion = InspeccionIngreso.objects.get(vehiculo_desarme=vehiculo, documento=None)
    assert inspeccion.vehiculo_id is None
    assert inspeccion.vehiculo_desarme_id == vehiculo.pk
    danos = list(inspeccion.danos.all())
    assert len(danos) == 1
    assert danos[0].zona == "capo"
    assert danos[0].tipo_dano == "golpe"


def test_editar_con_danos_carroceria_tambien_funciona(db, empresa_chile, user_logueado, marca_modelo):
    """Mismo escenario pero en edición (editar_vehiculo también llama a
    _guardar_danos_carroceria, con un VehiculoDesarme ya existente)."""
    rf = RequestFactory()
    marca, modelo = marca_modelo
    vehiculo = VehiculoDesarme.objects.create(
        empresa=empresa_chile, marca=marca, modelo=modelo, patente="DANOTEST2"
    )

    data = _datos_alta_con_danos(marca, modelo)
    data["patente"] = "DANOTEST2"
    request = _post(
        rf, f"/cl/es/desarme/vehiculos/{vehiculo.pk}/editar/", user_logueado, data
    )
    response = editar_vehiculo(request, pk=vehiculo.pk)

    assert response.status_code == 302, getattr(response, "content", b"").decode(
        "utf-8", errors="replace"
    )

    inspeccion = InspeccionIngreso.objects.get(vehiculo_desarme=vehiculo, documento=None)
    assert inspeccion.vehiculo_id is None
    assert inspeccion.vehiculo_desarme_id == vehiculo.pk


def test_alta_sin_danos_no_crea_inspeccion(db, empresa_chile, user_logueado, marca_modelo):
    """Sin sección de daños cargada, _guardar_danos_carroceria corta antes
    (if not zonas: return) -- no debe crear ninguna InspeccionIngreso."""
    rf = RequestFactory()
    marca, modelo = marca_modelo
    data = _datos_alta_con_danos(marca, modelo)
    data["patente"] = "SINDANOS1"
    del data["zona_0"], data["tipo_dano_0"], data["descripcion_0"]

    request = _post(rf, "/cl/es/desarme/vehiculos/crear/", user_logueado, data)
    response = crear_vehiculo(request)
    assert response.status_code == 302

    vehiculo = VehiculoDesarme.objects.get(empresa=empresa_chile, patente="SINDANOS1")
    assert not InspeccionIngreso.objects.filter(vehiculo_desarme=vehiculo).exists()
