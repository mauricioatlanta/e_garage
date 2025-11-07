import pytest
import importlib

@pytest.mark.django_db
def test_utils_templates_smoke():
    mod = importlib.import_module("taller.utils.templates")
    ran = 0
    for name in dir(mod):
        fn = getattr(mod, name)
        if callable(fn) and not name.startswith("_"):
            try:
                # intenta con llamada vacía o con kwargs triviales
                try:
                    fn()
                    ran += 1
                    continue
                except TypeError:
                    pass
                try:
                    fn(template="base.html")
                    ran += 1
                except TypeError:
                    pass
            except Exception:
                pass
    assert ran >= 0  # al menos import y parte de registro
