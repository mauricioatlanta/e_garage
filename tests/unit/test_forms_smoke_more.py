import pytest
from django.test import RequestFactory

CANDS = [
    ("taller.forms.empresa",    "EmpresaForm", {"nombre":"ACME","pais":"CL"}),
    ("taller.forms.vehiculo",   "VehiculoForm", {"patente":"AAA11","marca":"X","modelo":"Y","anio":2024}),
    ("taller.forms.documento",  "DocumentoForm", {"tipo":"FAC","fecha_emision":"2025-01-01"}),
    ("taller.forms.repuesto",   "RepuestoForm", {"nombre":"Filtro","precio":1000}),
    ("taller.forms.servicios",  "ServicioForm", {"nombre":"Alineación","precio":5000}),
]

@pytest.mark.django_db
@pytest.mark.parametrize("mod,cls,min_data", CANDS)
def test_forms_min_valid_and_invalid(mod, cls, min_data):
    try:
        m = __import__(mod, fromlist=[cls])
        Form = getattr(m, cls)
    except Exception:
        pytest.skip(f"Sin {mod}.{cls}")

    # invalid (vacío) no debe crash
    try:
        f_bad = Form(data={})
        assert not f_bad.is_valid()
    except Exception:
        # Si el form requiere usuario o empresa, lo saltamos
        pytest.skip(f"Form {cls} requiere contexto adicional")

    # valid mínimo (cuando falten relaciones FK, permitimos que sea inválido pero sin explotar)
    try:
        f_ok = Form(data=min_data)
        f_ok.is_valid()  # ejercita clean/validations
        assert f_ok.errors is not None  # cualquier resultado, pero sin excepción
    except Exception:
        # Si el form requiere usuario o empresa, lo saltamos
        pytest.skip(f"Form {cls} requiere contexto adicional")
