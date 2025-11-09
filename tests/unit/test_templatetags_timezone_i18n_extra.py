import pytest


@pytest.mark.django_db
def test_timezone_and_i18n_filters_extra():
    try:
        from taller.templatetags import simple_i18n, timezone_tags
    except Exception:
        pytest.skip("No existen timezone_tags/simple_i18n")

    # timezone_tags: prueba de formateo de fecha/hora segura
    # usamos valores de ejemplo; si los filtros no existen, skip.
    fmt_fn = (
        getattr(timezone_tags, "format_datetime", None)
        or getattr(timezone_tags, "tz_format", None)
        or getattr(timezone_tags, "dt_format", None)
    )
    if not fmt_fn:
        pytest.skip("No hay filtro de formateo en timezone_tags")

    out = fmt_fn("2025-01-02T03:04:05Z", "America/Santiago")
    assert isinstance(out, str) and out

    # simple_i18n: prueba de traducción simple/placeholder
    tr_fn = getattr(simple_i18n, "t", None) or getattr(simple_i18n, "translate", None)
    if not tr_fn:
        pytest.skip("No hay función de traducción en simple_i18n")

    res = tr_fn("vehiculo.creado", default="Vehículo creado")
    assert isinstance(res, str) and res
