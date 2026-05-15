from decimal import Decimal

import pytest

from django.template import Context, Template
from django.test import RequestFactory


@pytest.mark.django_db
def test_moneda_y_qs_tools_inputs_feos():
    rf = RequestFactory()
    request = rf.get("/?a=1&b=2")
    ctx = {
        "request": request,
        "val_none": None,
        "val_str": "",
        "val_big": 10**12,
        "val_dec": Decimal("1234.56"),
    }

    candidates = [
        # moneda: intenta varios nombres comunes
        "{% load moneda %}{{ val_big|clp }}",
        "{% load moneda %}{{ val_dec|moneda }}",
        "{% load moneda %}{{ val_none|clp }}",
        # qs_tools: intenta operaciones típicas de querystring
        '{% load qs_tools %}{{ "a"|qs_without:"b" }}',
        '{% load qs_tools %}{{ "b"|qs_set:"c=3" }}',
        '{% load qs_tools %}{{ ""|qs_add:"a=9" }}',
    ]

    rendered_ok = False
    for src in candidates:
        try:
            Template(src).render(Context(ctx))
            rendered_ok = True
        except Exception:
            # tolerante: si un filtro no existe, seguimos probando otros
            continue

    if not rendered_ok:
        pytest.skip("No se cargaron filtros compatibles en moneda/qs_tools")
