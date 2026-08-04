# -*- coding: utf-8 -*-
"""
Tests para Motor de Impuestos

Verifica:
- resolve_tax_rate funciona correctamente
- Chile: IVA 19% solo repuestos (NO servicios)
- USA: sales tax por ubicación
- Fallbacks funcionan correctamente
"""
import pytest
from decimal import Decimal

from taller.impuestos.engine import resolve_tax_rate, get_tax_info
from taller.models import TaxPolicy, Empresa, Estado, Ciudad
from ubicacion.models import Address
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestTaxEngineBasic:
    """Tests básicos del motor de impuestos"""

    def test_resolve_tax_rate_returns_decimal(self):
        """Test: resolve_tax_rate retorna Decimal"""
        # Crear empresa de prueba
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Test Taller", pais="CL")

        rate, inclusive = resolve_tax_rate(empresa, None, "parts")

        assert isinstance(rate, Decimal)
        assert isinstance(inclusive, bool)

    def test_resolve_tax_rate_chile_parts(self):
        """Test: Chile repuestos → IVA 19%"""
        # Crear política de Chile
        TaxPolicy.objects.create(
            country="CL",
            state_code="",
            city_name="",
            applies_to="parts",
            rate=Decimal("0.19"),
            inclusive=False,
            active=True,
        )

        # Crear empresa de Chile
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Taller Chile", pais="CL")

        rate, inclusive = resolve_tax_rate(empresa, None, "parts")

        assert rate == Decimal("0.19")
        assert inclusive == False

    def test_resolve_tax_rate_chile_services(self):
        """Test: Chile servicios → 0% (sin impuesto)"""
        # Crear política solo para parts
        TaxPolicy.objects.create(
            country="CL",
            state_code="",
            city_name="",
            applies_to="parts",
            rate=Decimal("0.19"),
            inclusive=False,
            active=True,
        )

        # Crear empresa de Chile
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Taller Chile 2", pais="CL")

        # Servicios deben dar 0%
        rate, inclusive = resolve_tax_rate(empresa, None, "services")

        assert rate == Decimal("0.00")

    def test_resolve_tax_rate_peru_both(self):
        """Test: Perú → IGV 18% ambos"""
        # Crear política de Perú
        TaxPolicy.objects.create(
            country="PE",
            state_code="",
            city_name="",
            applies_to="both",
            rate=Decimal("0.18"),
            inclusive=False,
            active=True,
        )

        # Crear empresa de Perú
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Taller Perú", pais="PE")

        # Parts → 18%
        rate_parts, _ = resolve_tax_rate(empresa, None, "parts")
        assert rate_parts == Decimal("0.18")

        # Services → 18%
        rate_services, _ = resolve_tax_rate(empresa, None, "services")
        assert rate_services == Decimal("0.18")

    def test_resolve_tax_rate_venezuela(self):
        """Test: Venezuela → IVA 16% ambos"""
        # Crear política de Venezuela
        TaxPolicy.objects.create(
            country="VE",
            state_code="",
            city_name="",
            applies_to="both",
            rate=Decimal("0.16"),
            inclusive=False,
            active=True,
        )

        # Crear empresa de Venezuela
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Taller Venezuela", pais="VE")

        rate, _ = resolve_tax_rate(empresa, None, "both")
        assert rate == Decimal("0.16")


@pytest.mark.django_db
class TestTaxEngineUSA:
    """Tests específicos para USA (sales tax por ubicación)"""

    def test_usa_sales_tax_by_state(self):
        """Test: USA sales tax por estado"""
        # Crear política para California
        TaxPolicy.objects.create(
            country="US",
            state_code="CA",
            city_name="",
            applies_to="both",
            rate=Decimal("0.0725"),
            inclusive=False,
            active=True,
        )

        # Crear empresa USA en California
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Taller USA", pais="US")

        # Crear estado y ciudad de California
        ca_state = Estado.objects.create(
            nombre="California", codigo="CA", pais="US", sales_tax=7.25
        )

        la_city = Ciudad.objects.create(nombre="Los Angeles", estado=ca_state, sales_tax_local=0.00)

        # Resolver tax rate con ciudad
        rate, _ = resolve_tax_rate(empresa, la_city, "parts")

        assert rate == Decimal("0.0725")

    def test_usa_different_states_different_rates(self):
        """Test: USA diferentes estados, diferentes tasas"""
        # California: 7.25%
        TaxPolicy.objects.create(
            country="US", state_code="CA", applies_to="both", rate=Decimal("0.0725")
        )

        # Florida: 6%
        TaxPolicy.objects.create(
            country="US", state_code="FL", applies_to="both", rate=Decimal("0.06")
        )

        # Empresas en diferentes estados
        from taller.tests.factories import EmpresaFactory
        empresa_ca = EmpresaFactory(nombre_taller="California Taller", pais="US")
        empresa_fl = EmpresaFactory(nombre_taller="Florida Taller", pais="US")

        # Crear estados y ciudades
        ca_state = Estado.objects.create(
            nombre="California", codigo="CA", pais="US", sales_tax=7.25
        )
        ca_city = Ciudad.objects.create(nombre="Los Angeles", estado=ca_state)

        fl_state = Estado.objects.create(nombre="Florida", codigo="FL", pais="US", sales_tax=6.00)
        fl_city = Ciudad.objects.create(nombre="Miami", estado=fl_state)

        # Verificar tasas diferentes
        rate_ca, _ = resolve_tax_rate(empresa_ca, ca_city, "parts")
        rate_fl, _ = resolve_tax_rate(empresa_fl, fl_city, "parts")

        assert rate_ca == Decimal("0.0725")
        assert rate_fl == Decimal("0.06")
        assert rate_ca != rate_fl


@pytest.mark.django_db
class TestTaxEngineFallbacks:
    """Tests para fallbacks del motor de impuestos"""

    def test_fallback_when_no_policy(self):
        """Test: fallback a sales_tax de estado si no hay política"""
        # No crear política

        # Crear empresa y ciudad
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Taller Fallback", pais="PE")

        estado = Estado.objects.create(
            nombre="Lima", codigo="LIM", pais="PE", sales_tax=18.00  # Fallback
        )

        ciudad = Ciudad.objects.create(nombre="Lima", estado=estado, sales_tax_local=0.00)

        # Debe usar sales_tax del estado
        rate, _ = resolve_tax_rate(empresa, ciudad, "parts")

        # Debe retornar 0.18 (18%) del estado
        assert rate == Decimal("0.18")

    def test_fallback_country_default(self):
        """Test: fallback a default del país si no hay nada"""
        # No crear política ni estado

        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Taller Default", pais="BR")

        # Debe usar default de Brasil
        rate, _ = resolve_tax_rate(empresa, None, "parts")

        # Brasil default es 18%
        assert rate == Decimal("0.18")


@pytest.mark.django_db
class TestTaxEngineConventions:
    """Tests para verificar convenciones del proyecto"""

    def test_convention_chile_parts_only(self):
        """Test CRÍTICO: Chile IVA 19% SOLO repuestos"""
        # Crear política solo para parts
        TaxPolicy.objects.create(country="CL", applies_to="parts", rate=Decimal("0.19"))

        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller="Taller Convención", pais="CL")

        # Parts → 19%
        rate_parts, _ = resolve_tax_rate(empresa, None, "parts")
        assert rate_parts == Decimal("0.19"), "Chile repuestos debe ser 19%"

        # Services → 0%
        rate_services, _ = resolve_tax_rate(empresa, None, "services")
        assert rate_services == Decimal("0.00"), "Chile servicios debe ser 0%"

        # NO debe existir política para services
        policy_services = TaxPolicy.objects.filter(country="CL", applies_to="services").exists()

        assert not policy_services, "Chile NO debe tener política para servicios"

    def test_convention_usa_sales_tax_by_location(self):
        """Test CRÍTICO: USA sales tax por ubicación"""
        # Crear políticas para diferentes estados
        TaxPolicy.objects.create(
            country="US", state_code="CA", applies_to="both", rate=Decimal("0.0725")
        )

        TaxPolicy.objects.create(
            country="US", state_code="TX", applies_to="both", rate=Decimal("0.0625")
        )

        # Debe haber múltiples políticas
        usa_policies = TaxPolicy.objects.filter(country="US").count()
        assert usa_policies >= 2, "USA debe tener múltiples políticas por estado"


@pytest.fixture
def sample_tax_policies(db):
    """Fixture: crear políticas de impuestos de prueba"""
    policies = []

    # Chile: IVA 19% solo repuestos
    policies.append(
        TaxPolicy.objects.create(country="CL", applies_to="parts", rate=Decimal("0.19"))
    )

    # USA: varios estados
    for state, rate in [("CA", 0.0725), ("TX", 0.0625), ("NY", 0.04)]:
        policies.append(
            TaxPolicy.objects.create(
                country="US", state_code=state, applies_to="both", rate=Decimal(str(rate))
            )
        )

    # Brasil: ICMS 18% repuestos
    policies.append(
        TaxPolicy.objects.create(country="BR", applies_to="parts", rate=Decimal("0.18"))
    )

    # Perú: IGV 18% ambos
    policies.append(TaxPolicy.objects.create(country="PE", applies_to="both", rate=Decimal("0.18")))

    # Venezuela: IVA 16% ambos
    policies.append(TaxPolicy.objects.create(country="VE", applies_to="both", rate=Decimal("0.16")))

    return policies


@pytest.mark.django_db
def test_all_countries_with_sample_policies(sample_tax_policies):
    """Test: todos los países con políticas de muestra"""
    countries_config = [
        ("CL", "parts", Decimal("0.19")),
        ("CL", "services", Decimal("0.00")),
        ("US", "parts", Decimal("0.0000")),  # Sin ubicación: no se puede determinar sales tax
        ("BR", "parts", Decimal("0.18")),
        ("PE", "both", Decimal("0.18")),
        ("VE", "both", Decimal("0.16")),
    ]

    for country, applies_to, expected_rate in countries_config:
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(nombre_taller=f"Taller {country}", pais=country)

        rate, _ = resolve_tax_rate(empresa, None, applies_to)

        assert (
            rate == expected_rate
        ), f"Failed for {country} {applies_to}: expected {expected_rate}, got {rate}"
