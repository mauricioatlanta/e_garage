"""
Tests para templatetags de money - cobertura rápida de filtros de formato
"""

from decimal import Decimal

from django.template import Context, Template
from django.test import TestCase

from taller.templatetags.money import _to_decimal, money_by_country, money_clp


class MoneyTemplatetagsTest(TestCase):
    """Tests para templatetags de money"""

    def test_to_decimal_valid_values(self):
        """Test función _to_decimal con valores válidos"""
        self.assertEqual(_to_decimal("123.45"), Decimal("123.45"))
        # Usar quantize para evitar problemas de precisión de float
        expected = Decimal("123.45")
        result = _to_decimal(123.45)
        self.assertEqual(result.quantize(expected), expected)
        self.assertEqual(_to_decimal(123), Decimal("123"))
        self.assertEqual(_to_decimal(Decimal("123.45")), Decimal("123.45"))

    def test_to_decimal_invalid_values(self):
        """Test función _to_decimal con valores inválidos"""
        self.assertEqual(_to_decimal("invalid"), Decimal("0"))
        self.assertEqual(_to_decimal(None), Decimal("0"))
        self.assertEqual(_to_decimal(""), Decimal("0"))
        self.assertEqual(_to_decimal("abc"), Decimal("0"))

    def test_money_clp_filter(self):
        """Test filtro money_clp"""
        # Test con número entero
        self.assertEqual(money_clp(12345), "$12.345")

        # Test con decimal (el filtro redondea, no trunca)
        self.assertEqual(money_clp(12345.67), "$12.346")

        # Test con string
        self.assertEqual(money_clp("12345"), "$12.345")

        # Test con valor inválido
        self.assertEqual(money_clp("invalid"), "$0")

        # Test con None
        self.assertEqual(money_clp(None), "$0")

    def test_money_by_country_chile(self):
        """Test filtro money_by_country para Chile"""
        # Test con país CL
        self.assertEqual(money_by_country(12345, "CL"), "$12.345")

        # Test sin especificar país (default CL)
        self.assertEqual(money_by_country(12345), "$12.345")

    def test_money_by_country_usa(self):
        """Test filtro money_by_country para USA"""
        # Test con país US
        self.assertEqual(money_by_country(12345.67, "US"), "$12,345.67")

        # Test con valor entero
        self.assertEqual(money_by_country(12345, "US"), "$12,345.00")

    def test_money_by_country_other(self):
        """Test filtro money_by_country para otros países"""
        # Test con país no reconocido (fallback USD)
        self.assertEqual(money_by_country(12345.67, "MX"), "$12,345.67")

    def test_money_clp_template_filter(self):
        """Test filtro money_clp en template"""
        template = Template("{% load money %}{{ value|money_clp }}")

        # Test con número
        context = Context({"value": 12345})
        result = template.render(context)
        self.assertEqual(result, "$12.345")

        # Test con string
        context = Context({"value": "12345"})
        result = template.render(context)
        self.assertEqual(result, "$12.345")

        # Test con valor inválido
        context = Context({"value": "invalid"})
        result = template.render(context)
        self.assertEqual(result, "$0")

    def test_money_by_country_template_filter(self):
        """Test filtro money_by_country en template"""
        template = Template("{% load money %}{{ value|money_by_country:country }}")

        # Test con Chile
        context = Context({"value": 12345, "country": "CL"})
        result = template.render(context)
        self.assertEqual(result, "$12.345")

        # Test con USA
        context = Context({"value": 12345.67, "country": "US"})
        result = template.render(context)
        self.assertEqual(result, "$12,345.67")

    def test_money_clp_large_numbers(self):
        """Test filtro money_clp con números grandes"""
        # Test con número grande
        self.assertEqual(money_clp(1234567), "$1.234.567")

        # Test con número muy grande
        self.assertEqual(money_clp(1234567890), "$1.234.567.890")

    def test_money_by_country_edge_cases(self):
        """Test filtro money_by_country con casos edge"""
        # Test con 0
        self.assertEqual(money_by_country(0, "CL"), "$0")
        self.assertEqual(money_by_country(0, "US"), "$0.00")

        # Test con número negativo
        self.assertEqual(money_by_country(-12345, "CL"), "$-12.345")
        self.assertEqual(money_by_country(-12345.67, "US"), "$-12,345.67")

    def test_money_clp_edge_cases(self):
        """Test filtro money_clp con casos edge"""
        # Test con 0
        self.assertEqual(money_clp(0), "$0")

        # Test con número negativo
        self.assertEqual(money_clp(-12345), "$-12.345")

        # Test con decimal muy pequeño
        self.assertEqual(money_clp(0.01), "$0")
