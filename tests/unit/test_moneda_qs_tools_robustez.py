import pytest
from decimal import Decimal
from django.template import Context, Template
from django.test import TestCase


class TestMonedaQsToolsRobustez(TestCase):
    """
    Test de robustez para moneda/qs_tools con inputs edge cases:
    - None, '', enteros enormes, Decimal y strings raros
    - Nunca debe explotar, siempre retorna un fallback razonable
    """

    def test_moneda_clp_edge_cases(self):
        """Test del filtro clp con inputs edge cases"""
        template = Template('{% load moneda %}{{ value|clp }}')
        
        test_cases = [
            (None, 'None'),  # None se convierte a string 'None'
            ('', ''),      # String vacío debe retornar string vacío
            ('abc', 'abc'),  # String no numérico debe retornar el string
            ('123.456', '$123'),  # Decimal debe redondearse
            (123.456, '$123'),    # Float debe redondearse
            (123, '$123'),        # Entero debe funcionar
            (999999999999, '$999.999.999.999'),  # Entero enorme
            (Decimal('123.789'), '$124'),  # Decimal object
            ('123.789', '$124'),  # String decimal
            (0, '$0'),            # Cero
            (-123.456, '$-123'),  # Negativo
        ]
        
        for input_value, expected in test_cases:
            with self.subTest(value=input_value):
                result = template.render(Context({'value': input_value}))
                self.assertEqual(result, expected, f"Failed for input: {input_value}")

    def test_money_clp_edge_cases(self):
        """Test del filtro money_clp con inputs edge cases"""
        template = Template('{% load money %}{{ value|money_clp }}')
        
        test_cases = [
            (None, '$0'),         # None debe retornar $0
            ('', '$0'),           # String vacío debe retornar $0
            ('abc', '$0'),        # String no numérico debe retornar $0
            ('123.456', '$123'),  # Decimal debe truncarse
            (123.456, '$123'),    # Float debe truncarse
            (123, '$123'),        # Entero debe funcionar
            (999999999999, '$999.999.999.999'),  # Entero enorme
            (Decimal('123.789'), '$124'),  # Decimal object - redondeado
            ('123.789', '$124'),  # String decimal - redondeado
            (0, '$0'),            # Cero
            (-123.456, '$-123'),  # Negativo
        ]
        
        for input_value, expected in test_cases:
            with self.subTest(value=input_value):
                result = template.render(Context({'value': input_value}))
                self.assertEqual(result, expected, f"Failed for input: {input_value}")

    def test_money_by_country_edge_cases(self):
        """Test del filtro money_by_country con inputs edge cases"""
        template_cl = Template('{% load money %}{{ value|money_by_country:"CL" }}')
        template_us = Template('{% load money %}{{ value|money_by_country:"US" }}')
        
        test_cases = [
            (None, '$0', '$0.00'),
            ('', '$0', '$0.00'),
            ('abc', '$0', '$0.00'),
            ('123.456', '$123', '$123.46'),
            (123.456, '$123', '$123.46'),
            (123, '$123', '$123.00'),
            (999999999999, '$999.999.999.999', '$999,999,999,999.00'),
            (Decimal('123.789'), '$124', '$123.79'),
            ('123.789', '$124', '$123.79'),
            (0, '$0', '$0.00'),
            (-123.456, '$-123', '$-123.46'),
        ]
        
        for input_value, expected_cl, expected_us in test_cases:
            with self.subTest(value=input_value):
                result_cl = template_cl.render(Context({'value': input_value}))
                result_us = template_us.render(Context({'value': input_value}))
                self.assertEqual(result_cl, expected_cl, f"CL failed for input: {input_value}")
                self.assertEqual(result_us, expected_us, f"US failed for input: {input_value}")

    def test_qs_count_edge_cases(self):
        """Test del filtro qs_count con inputs edge cases"""
        template = Template('{% load qs_tools %}{{ value|qs_count }}')
        
        # Mock queryset-like objects
        class MockQueryset:
            def count(self):
                return 42
        
        class MockQuerysetError:
            def count(self):
                raise Exception("Database error")
        
        class MockNonQueryset:
            def __len__(self):
                return 10
        
        test_cases = [
            (None, '0'),                    # None debe retornar 0
            ('', '0'),                      # String vacío debe retornar 0
            (123, '0'),                     # Entero debe retornar 0
            ([1, 2, 3], '0'),               # Lista debe retornar 0 (no tiene count())
            (MockQueryset(), '42'),         # Queryset válido debe retornar count()
            (MockQuerysetError(), '0'),     # Queryset con error debe retornar 0
            (MockNonQueryset(), '0'),       # Objeto sin count() debe retornar 0
        ]
        
        for input_value, expected in test_cases:
            with self.subTest(value=type(input_value).__name__):
                result = template.render(Context({'value': input_value}))
                self.assertEqual(result, expected, f"Failed for input: {input_value}")

    def test_moneda_filters_never_crash(self):
        """Test que los filtros de moneda nunca crasheen con inputs extremos"""
        template_clp = Template('{% load moneda %}{{ value|clp }}')
        template_money = Template('{% load money %}{{ value|money_clp }}')
        
        extreme_inputs = [
            float('inf'),           # Infinito
            float('-inf'),          # Infinito negativo
            float('nan'),           # Not a Number
            '1' * 1000,            # String muy largo
            '0' * 1000,            # String de ceros muy largo
            '9' * 1000,            # String de nueves muy largo
            '1.23' * 100,          # String decimal muy largo
            'abc' * 100,           # String no numérico muy largo
            {},                     # Diccionario vacío
            [],                     # Lista vacía
            set(),                  # Set vacío
            object(),               # Objeto genérico
        ]
        
        for extreme_input in extreme_inputs:
            with self.subTest(input=type(extreme_input).__name__):
                # No debe lanzar excepción
                try:
                    result_clp = template_clp.render(Context({'value': extreme_input}))
                    result_money = template_money.render(Context({'value': extreme_input}))
                    # Si llega aquí, el test pasa
                    self.assertTrue(True, f"Filter handled extreme input: {type(extreme_input).__name__}")
                except Exception as e:
                    self.fail(f"Filter crashed with extreme input {type(extreme_input).__name__}: {e}")

    def test_decimal_precision_handling(self):
        """Test manejo de precisión decimal en filtros de moneda"""
        template = Template('{% load money %}{{ value|money_clp }}')
        
        precision_cases = [
            (Decimal('123.1'), '$123'),
            (Decimal('123.5'), '$124'),  # Redondeado hacia arriba
            (Decimal('123.9'), '$124'),  # Redondeado hacia arriba
            (Decimal('123.0'), '$123'),
            (Decimal('0.1'), '$0'),
            (Decimal('0.5'), '$0'),      # Truncado (no redondeado)
            (Decimal('0.9'), '$1'),      # Redondeado hacia arriba
        ]
        
        for input_value, expected in precision_cases:
            with self.subTest(value=input_value):
                result = template.render(Context({'value': input_value}))
                self.assertEqual(result, expected, f"Precision failed for input: {input_value}")
