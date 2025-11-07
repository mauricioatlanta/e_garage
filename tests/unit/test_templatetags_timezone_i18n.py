import re
from django.test import TestCase
from django.template import Template, Context
from django.utils import timezone

def _render(tpl, ctx=None):
    return Template(tpl).render(Context(ctx or {}))

class TemplatetagsTimezoneI18nTest(TestCase):
    def test_timezone_tags_format_specific(self):
        # Fija zona horaria y verifica patrón de salida (YYYY-mm-dd HH:MM)
        timezone.activate("America/Santiago")
        out = _render('{% load timezone_tags %}{% now "Y-m-d H:i" as ts %}{{ ts }}')
        self.assertRegex(out.strip(), r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")

    def test_simple_i18n_filter_fallback_and_plain_text(self):
        # Test del filtro es_usa con None
        out = _render('{% load simple_i18n %}{{ None|es_usa }}')
        self.assertIn("False", out)  # Sin usuario, debería ser False
        
        # Test del filtro es_chile con None
        out2 = _render('{% load simple_i18n %}{{ None|es_chile }}')
        self.assertIn("False", out2)  # Sin usuario, debería ser False
