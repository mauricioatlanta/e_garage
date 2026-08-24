"""
Tests para la especialización de RECYCLING (Fase 304):
ConfiguracionEmpresa.recycling_type_principal / recycling_types.

Mismo convenio que rubro_principal/rubros (get_effective_rubros): la
especialidad principal siempre va primero en get_effective_recycling_types(),
seguida de las adicionales sin duplicar.
"""
import pytest

from taller.models.configuracion import ConfiguracionEmpresa
from taller.tests.factories import ConfiguracionEmpresaFactory


def test_recycling_type_choices_incluye_las_5_especialidades():
    values = [value for value, _ in ConfiguracionEmpresa.RECYCLING_TYPE_CHOICES]
    assert values == [
        "METAL_RECYCLING",
        "CATALYTIC_RECYCLING",
        "ELECTRONIC_SCRAP",
        "AUTO_PARTS_RECYCLING",
        "INDUSTRIAL_SCRAP",
    ]


@pytest.mark.django_db
class TestGetEffectiveRecyclingTypes:
    def test_vacio_si_no_hay_recycling_type_principal(self):
        config = ConfiguracionEmpresaFactory(rubro_principal="WORKSHOP")
        assert config.get_effective_recycling_types() == []

    def test_devuelve_solo_el_principal_si_no_hay_adicionales(self):
        config = ConfiguracionEmpresaFactory(
            rubro_principal="RECYCLING",
            recycling_type_principal="METAL_RECYCLING",
        )
        assert config.get_effective_recycling_types() == ["METAL_RECYCLING"]

    def test_principal_siempre_primero_sin_duplicar(self):
        config = ConfiguracionEmpresaFactory(
            rubro_principal="RECYCLING",
            recycling_type_principal="CATALYTIC_RECYCLING",
            recycling_types=["ELECTRONIC_SCRAP", "CATALYTIC_RECYCLING"],
        )
        assert config.get_effective_recycling_types() == [
            "CATALYTIC_RECYCLING",
            "ELECTRONIC_SCRAP",
        ]

    def test_caso_atlanta_catalitico_y_electronico(self):
        config = ConfiguracionEmpresaFactory(
            rubro_principal="RECYCLING",
            recycling_type_principal="CATALYTIC_RECYCLING",
            recycling_types=["CATALYTIC_RECYCLING", "ELECTRONIC_SCRAP"],
        )
        assert config.get_effective_recycling_types() == [
            "CATALYTIC_RECYCLING",
            "ELECTRONIC_SCRAP",
        ]
        # No debe filtrarse ninguna especialidad de metal/industrial genérica
        # que Atlanta no ofrece.
        assert "METAL_RECYCLING" not in config.get_effective_recycling_types()
        assert "INDUSTRIAL_SCRAP" not in config.get_effective_recycling_types()
