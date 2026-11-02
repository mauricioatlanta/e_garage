"""
Pin del mapeo de datos de la migración 0150_normalizar_estado_desarme.

Importa la migración directamente (por nombre de archivo, vía importlib, ya
que los módulos de migración empiezan con dígitos y no son importables con
`import` normal) y corre su MAPEO_FORWARD/forwards()/backwards() reales sobre
una base de datos de test -- no reimplementa el mapeo, así que un cambio en
la migración que rompa el mapeo hace fallar este test.
"""

import importlib

import pytest
from django.apps import apps as django_apps

from taller.models.vehiculo_desarme import ESTADO_DESARME_CHOICES, VehiculoDesarme
from taller.models.vehiculos import Vehiculo

migration_0150 = importlib.import_module("taller.migrations.0150_normalizar_estado_desarme")

# Valores históricos confirmados por Mauricio (no inferidos) que existían
# antes de esta migración, con su valor esperado tras normalizar.
VALORES_HISTORICOS_CONOCIDOS = {
    "EN_DESARME": "DESARMANDO",
    "en_yarda": "INGRESADO",
    "ACTIVO": "DESARMANDO",
    "en_proceso": "DESARMANDO",
}


def test_mapeo_forward_no_cambio_sin_avisar():
    """Si alguien edita MAPEO_FORWARD en la migración sin querer, esto lo marca."""
    assert migration_0150.MAPEO_FORWARD == VALORES_HISTORICOS_CONOCIDOS


def test_choices_validas_del_modulo_siguen_sincronizadas_con_el_modelo():
    """La migración duplica los choices a propósito (no importa el modelo real);
    este test es la alarma si el modelo cambia y la migración queda desactualizada."""
    choices_modelo = {valor for valor, _ in ESTADO_DESARME_CHOICES}
    assert migration_0150.CHOICES_VALIDAS_MODELO == choices_modelo


@pytest.mark.parametrize("valor_viejo,valor_esperado", list(VALORES_HISTORICOS_CONOCIDOS.items()))
def test_forwards_normaliza_cada_valor_historico_conocido(db, empresa_chile, valor_viejo, valor_esperado):
    vehiculo = Vehiculo.objects.create(
        empresa=empresa_chile,
        tipo_uso=Vehiculo.TIPO_USO_DESARME,
        patente=f"T{valor_viejo[:9]}",
        estado_desarme=valor_viejo,
    )
    vehiculo_desarme = VehiculoDesarme.objects.create(
        empresa=empresa_chile,
        vehiculo_origen_id=vehiculo.id,
        patente=vehiculo.patente,
        estado_desarme=valor_viejo,
    )

    migration_0150.forwards(django_apps, None)

    vehiculo.refresh_from_db()
    vehiculo_desarme.refresh_from_db()
    assert vehiculo.estado_desarme == valor_esperado
    assert vehiculo_desarme.estado_desarme == valor_esperado


def test_forwards_no_toca_valores_ya_validos_ni_vacios_ni_null(db, empresa_chile):
    vd_valido = VehiculoDesarme.objects.create(
        empresa=empresa_chile, patente="TVALIDO", estado_desarme="DESARMADO"
    )
    vd_vacio = VehiculoDesarme.objects.create(empresa=empresa_chile, patente="TVACIO", estado_desarme="")
    vd_none = VehiculoDesarme.objects.create(empresa=empresa_chile, patente="TNONE", estado_desarme=None)

    migration_0150.forwards(django_apps, None)

    vd_valido.refresh_from_db()
    vd_vacio.refresh_from_db()
    vd_none.refresh_from_db()
    assert vd_valido.estado_desarme == "DESARMADO"
    assert vd_vacio.estado_desarme == ""
    assert vd_none.estado_desarme is None


def test_forwards_deja_sin_tocar_valor_no_reconocido(db, empresa_chile):
    """Un valor que no está ni en el mapeo ni ya es choice válida se deja como está
    (se loguea aparte con logger.warning; acá solo verificamos que no lo pisa)."""
    vd = VehiculoDesarme.objects.create(
        empresa=empresa_chile, patente="TRARO", estado_desarme="ALGO_QUE_NO_VIMOS"
    )

    migration_0150.forwards(django_apps, None)

    vd.refresh_from_db()
    assert vd.estado_desarme == "ALGO_QUE_NO_VIMOS"


def test_backwards_revierte_al_representante_documentado(db, empresa_chile):
    """La reversa no es lossless (varios valores colapsan a DESARMANDO hacia
    adelante); solo puede reconstruir un representante único por cada choice
    del modelo. Este test fija ese comportamiento documentado, no lo esconde."""
    vd_desarmando = VehiculoDesarme.objects.create(
        empresa=empresa_chile, patente="TBACK1", estado_desarme="DESARMANDO"
    )
    vd_ingresado = VehiculoDesarme.objects.create(
        empresa=empresa_chile, patente="TBACK2", estado_desarme="INGRESADO"
    )

    migration_0150.backwards(django_apps, None)

    vd_desarmando.refresh_from_db()
    vd_ingresado.refresh_from_db()
    assert vd_desarmando.estado_desarme == "en_proceso"
    assert vd_ingresado.estado_desarme == "en_yarda"
