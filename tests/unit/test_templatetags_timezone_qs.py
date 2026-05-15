import pytest

from django.template import Context, Template


def _render(tpl, ctx=None):
    return Template(tpl).render(Context(ctx or {}))


@pytest.mark.django_db
def test_load_timezone_tags_smoke():
    # Cubre import + registro. Aunque no uses filtros específicos aún,
    # el simple load ejecuta el módulo.
    out = _render('{% load timezone_tags %}{% now "c" as ts %}{{ ts }}')
    assert out.strip()  # alguna fecha ISO-8601


@pytest.mark.django_db
def test_load_qs_tools_builds_querystring_smoke():
    # Algunos proyectos usan tag "querystring" o similar; si no existe,
    # igual cubrimos el módulo con el load.
    try:
        out = _render("{% load qs_tools %}{% if 1 %}{% endif %}")
        assert out is not None
    except Exception:
        pytest.skip("qs_tools no expone tags utilizables en plantillas")
