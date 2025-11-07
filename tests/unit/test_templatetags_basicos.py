from django.test import TestCase
from django.template import Context, Template
from decimal import Decimal


class TemplatetagsBasicosTest(TestCase):
    """Tests básicos para templatetags"""

    def test_money_clp_filter(self):
        """Test filtro money_clp"""
        tpl = Template('{% load money %}{{ 123456|money_clp }}')
        out = tpl.render(Context({}))
        assert "123" in out
        assert "$" in out

    def test_money_by_country_filter(self):
        """Test filtro money_by_country"""
        tpl = Template('{% load money %}{{ 123456|money_by_country:"CL" }}')
        out = tpl.render(Context({}))
        assert "123" in out
        assert "$" in out

    def test_math_multiply_filter(self):
        """Test filtro multiply"""
        tpl = Template('{% load math_filters %}{{ 10|multiply:5 }}')
        out = tpl.render(Context({}))
        assert "50" in out

    def test_math_filters_basic(self):
        """Test filtros matemáticos básicos"""
        tpl = Template('{% load math_filters %}{{ 10|multiply:2 }}')
        out = tpl.render(Context({}))
        assert "20" in out

    def test_simple_i18n_safe_smoke(self):
        """Test filtro i18n básico"""
        tpl = Template('{% load simple_i18n %}{{ "Hola"|safe }}')
        out = tpl.render(Context({}))
        assert "Hola" in out