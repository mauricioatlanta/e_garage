"""
Tests para ConfiguracionEmpresa.get_secciones_visibles()/get_ui_config() —
qué secciones del formulario de documentos se muestran según el rubro.

Contexto: reportado para RECYCLING (Atlanta Reciclajes) — el formulario de
"Nuevo Documento" mostraba una sección de VEHÍCULO (selector, kilometraje)
como cualquier taller mecánico, aunque una compra de reciclaje nunca está
asociada al vehículo de un cliente. La causa: `usa_vehiculos` es un campo
booleano con default=True a nivel de modelo, y ningún rubro lo desactivaba
nunca — ni siquiera "PARTS" (Casa de Repuestos), que tiene el mismo
problema latente sin haber sido reportado todavía.
"""

import pytest

from taller.tests.factories import ConfiguracionEmpresaFactory


@pytest.mark.django_db
def test_recycling_oculta_vehiculo_servicios_kilometraje():
    config = ConfiguracionEmpresaFactory(rubro_principal="RECYCLING")

    secciones = config.get_secciones_visibles()
    assert secciones["vehiculo"] is False
    assert secciones["servicios"] is False
    assert secciones["otros_servicios"] is False
    assert secciones["kilometraje"] is False
    assert secciones["repuestos"] is True

    ui_config = config.get_ui_config()
    assert ui_config["show_vehicle"] is False
    assert ui_config["show_services"] is False
    assert ui_config["show_kilometraje"] is False
    assert ui_config["show_repuestos"] is True


@pytest.mark.django_db
def test_recycling_oculta_vehiculo_aunque_usa_vehiculos_este_en_true():
    """El override por rubro debe ganar incluso si el flag manual de la
    empresa (heredado del default a nivel de modelo) sigue en True."""
    config = ConfiguracionEmpresaFactory(rubro_principal="RECYCLING", usa_vehiculos=True)
    assert config.get_ui_config()["show_vehicle"] is False


@pytest.mark.django_db
def test_workshop_sigue_mostrando_vehiculo_por_defecto():
    """Regresión: el rubro WORKSHOP (el caso común, taller mecánico) no
    debe perder la sección de vehículo al agregar el override de RECYCLING."""
    config = ConfiguracionEmpresaFactory(rubro_principal="WORKSHOP")
    assert config.get_ui_config()["show_vehicle"] is True


@pytest.mark.django_db
def test_parts_no_afectado_por_el_cambio():
    """Regresión: PARTS ya ocultaba servicios/kilometraje; ese
    comportamiento no debe cambiar (su 'vehiculo' sigue sin override
    explícito — comportamiento preexistente, fuera de alcance de este fix)."""
    config = ConfiguracionEmpresaFactory(rubro_principal="PARTS")
    secciones = config.get_secciones_visibles()
    assert secciones["servicios"] is False
    assert secciones["otros_servicios"] is False
    assert secciones["kilometraje"] is False
