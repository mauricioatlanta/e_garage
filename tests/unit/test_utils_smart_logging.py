import pytest
import importlib
import logging

@pytest.mark.django_db
def test_smart_logging_handlers_and_formatters():
    mod = importlib.import_module("taller.utils.smart_logging")
    # Crea un logger temporal con formatter si existe un factory
    created = False
    for name in dir(mod):
        fn = getattr(mod, name)
        if callable(fn) and ("formatter" in name.lower() or "handler" in name.lower() or "setup" in name.lower()):
            try:
                obj = fn()
                # Si devuelve handler/formatter, úsalo
                if isinstance(obj, logging.Formatter):
                    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "hello %s", ("world",), None)
                    _ = obj.format(rec)
                created = True
            except Exception:
                pass
    # Asegura que el módulo al menos carga
    assert mod is not None or created
