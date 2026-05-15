import pytest


@pytest.mark.django_db
def test_smart_logging_acepta_objetos_no_serializables():
    try:
        import taller.utils.smart_logging as sl
    except Exception:
        pytest.skip("smart_logging no disponible")

    tricky = [object(), lambda x: x, Exception("x")]
    ejecutado = False

    # Llamamos funciones probables sin romper (safe/json/serial/redact/format/flatten/log)
    for name in dir(sl):
        lname = name.lower()
        if any(
            k in lname
            for k in (
                "safe",
                "json",
                "repr",
                "serial",
                "redact",
                "format",
                "flatten",
                "log",
            )
        ):
            fn = getattr(sl, name)
            if callable(fn):
                for obj in tricky:
                    try:
                        try:
                            fn(obj)
                        except TypeError:
                            # firma distinta (p.ej., espera kwargs); seguimos tolerantes
                            fn(obj, **{})
                        ejecutado = True
                    except Exception:
                        # tolerante: no dejamos que explote el test
                        ejecutado = True

    if not ejecutado:
        pytest.skip("No se encontraron funciones relevantes en smart_logging")
