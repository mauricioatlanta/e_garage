"""
Fase 6.2 punto 6 + Fase 6.3b -- test end-to-end completo, sin pasar por
ningún Vehiculo intermedio en ningún momento:

  ajax_agregar_motor/caja (privados nuevos)
    -> crear_vehiculo (país USA, sin cliente)
    -> inicializar_sugerencias
    -> finalizar_sesion
    -> inventario_inteligente
    -> crear_venta_desde_inventario
    -> confirmar_venta_desde_inventario
    -> finalizar_venta_desde_inventario

Todas las vistas se llaman directamente (RequestFactory), no vía Client:
evita el middleware de excepciones/logging de Django, que en este entorno
(Django 4.2 + Python 3.14) rompe con un AttributeError propio de
django.test.client al renderizar una plantilla de traceback -- no es un bug
del código bajo prueba (ver Fase 5). Las vistas JSON (ajax_*) tampoco tienen
ese problema porque no renderizan templates.
"""

import json

import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from taller.desarme.services import inicializar_sugerencias
from taller.desarme.views import crear_vehiculo, revisar_vehiculo
from taller.desarme.views_inventario import (
    VENTA_SESSION_KEY,
    confirmar_venta_desde_inventario,
    crear_venta_desde_inventario,
    finalizar_venta_desde_inventario,
    inventario_inteligente,
)
from taller.models.documento import Documento
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.pieza_desarme import PiezaDesarme
from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo
from taller.vehiculos.views_fbv import ajax_agregar_caja, ajax_agregar_motor


@pytest.fixture
def user_usa(empresa_usa):
    empresa_usa.user.empresa = empresa_usa
    return empresa_usa.user


@pytest.fixture
def marca_modelo_usa(db):
    marca = Marca.objects.create(country="US", nombre="E2E Marca USA Fase6")
    modelo = Modelo.objects.create(country="US", marca=marca, nombre="E2E Modelo USA Fase6")
    return marca, modelo


def _get(rf, path, user, session=None):
    request = rf.get(path)
    request.user = user
    request.session = session if session is not None else SessionStore()
    if not request.session.session_key:
        request.session.create()
    request._messages = FallbackStorage(request)
    return request


def _post(rf, path, user, data=None, session=None, content_type=None):
    if content_type:
        request = rf.post(path, data=data, content_type=content_type)
    else:
        request = rf.post(path, data=data or {})
    request.user = user
    request.session = session if session is not None else SessionStore()
    if not request.session.session_key:
        request.session.create()
    request._messages = FallbackStorage(request)
    return request


def test_alta_desarme_completa_hasta_venta_sin_pasar_por_vehiculo(
    db, empresa_usa, user_usa, marca_modelo_usa
):
    rf = RequestFactory()
    marca, modelo = marca_modelo_usa

    # 1) Motor y caja privados nuevos, vía AJAX (mismo flujo que dispara el JS
    #    del template tras Fase 2).
    req_motor = _post(
        rf,
        "/us/vehiculos/ajax/agregar-motor/",
        user_usa,
        data=json.dumps({"nombre": "Motor E2E Fase6", "modelo_id": modelo.pk}),
        content_type="application/json",
    )
    resp_motor = ajax_agregar_motor(req_motor)
    motor_payload = json.loads(resp_motor.content)
    assert motor_payload["success"], motor_payload
    motor_value = motor_payload["motor"]["id"]
    assert motor_value.startswith("empresa:")

    req_caja = _post(
        rf,
        "/us/vehiculos/ajax/agregar-caja/",
        user_usa,
        data=json.dumps({"nombre": "Caja E2E Fase6", "modelo_id": modelo.pk}),
        content_type="application/json",
    )
    resp_caja = ajax_agregar_caja(req_caja)
    caja_payload = json.loads(resp_caja.content)
    assert caja_payload["success"], caja_payload
    caja_value = caja_payload["caja"]["id"]

    # 2) Alta del vehículo de desarme: país USA, sin cliente, con los privados.
    vin = "1FAFP404X1F123456"
    data_alta = {
        "patente": "",
        "vin": vin,
        "marca": str(marca.pk),
        "modelo": str(modelo.pk),
        "anio": "2021",
        "motor": motor_value,
        "caja": caja_value,
        "color": "",
        "tipo_carroceria": "",
        "estado_desarme": "INGRESADO",
    }
    req_crear = _post(rf, "/us/desarme/vehiculos/crear/", user_usa, data=data_alta)
    resp_crear = crear_vehiculo(req_crear)
    assert resp_crear.status_code == 302, getattr(resp_crear, "content", b"").decode(
        "utf-8", errors="replace"
    )

    # Nunca se creó un Vehiculo -- todo el flujo pasó por VehiculoDesarme directo.
    assert not Vehiculo.objects.filter(empresa=empresa_usa, vin=vin).exists()

    vehiculo = VehiculoDesarme.objects.get(empresa=empresa_usa, vin=vin)
    assert vehiculo.vehiculo_origen_id is None  # creado directo, no migrado
    assert vehiculo.motor_id is None
    assert vehiculo.motor_empresa_id is not None
    assert vehiculo.caja_id is None
    assert vehiculo.caja_empresa_id is not None
    assert f"/vehiculos/{vehiculo.pk}/revisar/" in resp_crear["Location"]

    # 3) crear_vehiculo ya inicializa las sugerencias del catálogo.
    sugerencias = list(
        SugerenciaPiezaDesarme.objects.filter(
            empresa=empresa_usa,
            vehiculo_desarme=vehiculo,
        )
    )
    assert sugerencias
    creadas = len(sugerencias)

    # La inicialización es idempotente y no debe duplicar registros.
    assert inicializar_sugerencias(vehiculo, empresa_usa) == 0
    assert SugerenciaPiezaDesarme.objects.filter(
        empresa=empresa_usa,
        vehiculo_desarme=vehiculo,
    ).count() == creadas

    SugerenciaPiezaDesarme.objects.filter(
        empresa=empresa_usa,
        vehiculo_desarme=vehiculo,
    ).update(
        estado=SugerenciaPiezaDesarme.CONFIRMADA,
        precio_sugerido=100,
        condicion_sugerida="BUENA",
    )

    req_finalizar_sesion = _post(
        rf,
        f"/us/en/desarme/vehiculos/{vehiculo.pk}/revisar/",
        user_usa,
        data=json.dumps({"action": "finalizar_sesion"}),
        content_type="application/json",
    )
    resp_finalizar_sesion = revisar_vehiculo(
        req_finalizar_sesion,
        pk=vehiculo.pk,
    )
    payload_finalizar = json.loads(resp_finalizar_sesion.content)
    assert resp_finalizar_sesion.status_code == 200, payload_finalizar
    assert payload_finalizar["success"] is True
    assert payload_finalizar["piezas_creadas"] == creadas

    piezas = list(
        PiezaDesarme.objects.filter(
            vehiculo_desarme=vehiculo,
            activo=True,
        )
    )
    assert len(piezas) == creadas

    for p in piezas:
        p.cantidad = 3
        p.precio_venta_sugerido = p.precio_venta_sugerido or 100
        p.save(update_fields=["cantidad", "precio_venta_sugerido"])

    # 4) inventario_inteligente: arma el grid de piezas del vehículo.
    req_inv = _get(rf, f"/desarme/vehiculos/{vehiculo.pk}/inventario-inteligente/", user_usa)
    resp_inv = inventario_inteligente(req_inv, pk=vehiculo.pk)
    assert resp_inv.status_code == 200

    # 5) crear_venta_desde_inventario: selecciona una pieza y arma la sesión de venta.
    pieza = piezas[0]
    session = SessionStore()
    session.create()
    selected = json.dumps([{"id": pieza.pk, "cantidad": 1, "precio_venta": "150"}])
    req_venta = _post(
        rf,
        f"/desarme/vehiculos/{vehiculo.pk}/crear-venta-desde-inventario/",
        user_usa,
        data={"selected_data": selected},
        session=session,
    )
    resp_venta = crear_venta_desde_inventario(req_venta, pk=vehiculo.pk)
    assert resp_venta.status_code == 302, "selected_data no generó una línea válida"
    assert session.get(VENTA_SESSION_KEY, {}).get("vehiculo_id") == vehiculo.pk

    # 6) confirmar_venta_desde_inventario: pantalla de revisión antes de finalizar.
    req_confirmar = _get(
        rf,
        f"/desarme/vehiculos/{vehiculo.pk}/confirmar-venta-desde-inventario/",
        user_usa,
        session=session,
    )
    resp_confirmar = confirmar_venta_desde_inventario(req_confirmar, pk=vehiculo.pk)
    assert resp_confirmar.status_code == 200

    # 7) finalizar_venta_desde_inventario: crea el documento y descuenta stock.
    #    Documento.vehiculo_desarme (Fase 6.3b) reemplaza a Documento.vehiculo
    #    para este caso -- ya no hay Vehiculo real detrás.
    req_finalizar = _post(
        rf,
        f"/desarme/vehiculos/{vehiculo.pk}/finalizar-venta-desde-inventario/",
        user_usa,
        data={"cliente_nombre": "Cliente Rapido E2E Fase6"},
        session=session,
    )
    resp_finalizar = finalizar_venta_desde_inventario(req_finalizar, pk=vehiculo.pk)
    assert resp_finalizar.status_code == 302, getattr(resp_finalizar, "content", b"").decode(
        "utf-8", errors="replace"
    )

    pieza.refresh_from_db()
    assert pieza.cantidad == 2  # 3 - 1 vendida

    documento = Documento.objects.get(empresa=empresa_usa, tipo="PTS", vehiculo_desarme=vehiculo)
    assert documento.vehiculo_id is None
    assert documento.vehiculo_desarme_id == vehiculo.pk
    assert VENTA_SESSION_KEY not in session
