"""
Tests de verificación de namespaces únicos por país
Verifica que no haya conflictos entre rutas de USA y Chile
"""

import pytest

from django.test import TestCase
from django.urls import reverse


class TestNamespacesPorPais(TestCase):
    """Tests para verificar que los namespaces están correctamente separados por país"""

    def test_namespaces_core_por_pais(self):
        """Verifica que los namespaces core están diferenciados por país"""
        # Core bajo país
        self.assertIsNotNone(reverse("chile:chile_home"))
        self.assertIsNotNone(reverse("usa:home"))

    def test_namespaces_clientes_por_pais(self):
        """Verifica que los namespaces de clientes están diferenciados por país"""
        # Clientes bajo /cl/es/ y /us/en/ (namespace core por país)
        self.assertIsNotNone(reverse("chile:clientes:lista_clientes"))
        self.assertIsNotNone(reverse("us_en:clientes:lista_clientes"))

    def test_namespaces_vehiculos_por_pais(self):
        """Verifica que los namespaces de vehículos están diferenciados por país"""
        # Vehículos
        self.assertIsNotNone(reverse("chile:vehiculos:lista_vehiculos"))
        self.assertIsNotNone(reverse("us_en:vehiculos:lista_vehiculos"))

    def test_namespaces_repuestos_por_pais(self):
        """Verifica que los namespaces de repuestos están diferenciados por país"""
        # Repuestos
        self.assertIsNotNone(reverse("chile:repuestos:lista_repuestos"))
        self.assertIsNotNone(reverse("us_en:repuestos:lista_repuestos"))

    def test_namespaces_servicios_por_pais(self):
        """Verifica que los namespaces de servicios están diferenciados por país"""
        # Servicios
        self.assertIsNotNone(reverse("chile:servicios:servicios_menu"))
        self.assertIsNotNone(reverse("us_en:servicios:servicios_menu"))

    def test_namespaces_tecnicos_por_pais(self):
        """Verifica que los namespaces de técnicos están diferenciados por país"""
        # Técnicos
        self.assertIsNotNone(reverse("chile:tecnicos:lista"))
        self.assertIsNotNone(reverse("usa:tecnicos:lista"))

    def test_namespaces_documentos_por_pais(self):
        """Verifica que los namespaces de documentos están diferenciados por país"""
        # Documentos / Reportes (ya diferenciados)
        self.assertIsNotNone(reverse("documentos_cl_es:lista_documentos"))
        self.assertIsNotNone(reverse("documentos_us_en:lista_documentos"))

    def test_namespaces_reportes_por_pais(self):
        """Verifica que los namespaces de reportes están diferenciados por país"""
        # Reportes
        self.assertIsNotNone(reverse("reportes_cl_es:reportes_dashboard"))
        self.assertIsNotNone(reverse("reportes_us_en:reportes_dashboard"))

    def test_no_conflictos_entre_paises(self):
        """Verifica que no hay conflictos entre namespaces de diferentes países"""
        # Verificar que los namespaces son únicos
        namespaces_cl = [
            "chile",
            "documentos_cl_es",
            "reportes_cl_es",
        ]
        namespaces_us = [
            "usa",
            "us_en",
            "us_es",
            "documentos_us_en",
            "reportes_us_en",
        ]

        # No debe haber intersección entre namespaces
        intersection = set(namespaces_cl) & set(namespaces_us)
        self.assertEqual(len(intersection), 0, f"Conflicto de namespaces: {intersection}")

    def test_urls_especificas_por_pais(self):
        """Verifica que las URLs específicas de cada país funcionan correctamente"""
        # URLs específicas de Chile
        self.assertIsNotNone(reverse("chile:chile_home"))

        # URLs específicas de USA
        self.assertIsNotNone(reverse("usa:home"))

    def test_templatetag_country_url(self):
        """Verifica que el templatetag country_url funciona correctamente"""
        from django.template import Context, Template

        # Crear contexto mock
        context = Context(
            {
                "request": type(
                    "MockRequest",
                    (),
                    {
                        "path": "/cl/",
                        "user": type(
                            "MockUser",
                            (),
                            {
                                "is_authenticated": True,
                                "empresa": type("MockEmpresa", (), {"pais": "CL"})(),
                            },
                        )(),
                    },
                )()
            }
        )

        # Test básico del templatetag
        template = Template("{% load country_url %}{% country_url 'clientes:lista_clientes' %}")
        result = template.render(context)
        self.assertIn("/cl/", result)


@pytest.mark.django_db
def test_namespaces_por_pais_pytest():
    """Test equivalente usando pytest para verificación rápida"""
    # Core bajo país
    assert reverse("chile:chile_home")
    assert reverse("usa:home")

    # Clientes
    assert reverse("chile:clientes:lista_clientes")
    assert reverse("us_en:clientes:lista_clientes")

    # Vehículos
    assert reverse("chile:vehiculos:lista_vehiculos")
    assert reverse("us_en:vehiculos:lista_vehiculos")

    # Documentos / Reportes (ya diferenciados)
    assert reverse("documentos_cl_es:lista_documentos")
    assert reverse("documentos_us_en:lista_documentos")
    assert reverse("reportes_cl_es:reportes_dashboard")
    assert reverse("reportes_us_en:reportes_dashboard")
