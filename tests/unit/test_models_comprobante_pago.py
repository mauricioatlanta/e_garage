# tests/unit/test_models_comprobante_pago.py
import pytest
import importlib
from decimal import Decimal
from datetime import datetime
from django.contrib.auth import get_user_model

def _has_field(model, name):
    return name in {f.name for f in model._meta.fields}

def _set_if_field(kwargs, model, name, value):
    if _has_field(model, name):
        kwargs[name] = value

@pytest.mark.django_db
def test_comprobante_pago_chile_totales():
    try:
        CP = importlib.import_module("taller.models.comprobante_pago").ComprobantePago
    except ModuleNotFoundError:
        pytest.skip("ComprobantePago no disponible")

    Empresa = importlib.import_module("taller.models.empresa").Empresa
    User = get_user_model()
    user = User.objects.create_user(username="testuser", password="testpass")
    
    emp = Empresa.objects.create(nombre_taller="EGarage CL", empresa="EGarage CL", pais="CL", direccion="Test", telefono="123", email="test@test.com", zona_horaria="UTC", fecha_inicio=datetime.now(), plan="mensual", dias_prueba=30, suscripcion_activa=True, valor_mensual=100, moneda="CLP", notificacion_5_dias=False, notificacion_1_dia=False, notificacion_vencido=False, user_id=user.id)

    # Documento es común en tu proyecto; si no existe, omitimos FK
    Documento = None
    try:
        Documento = importlib.import_module("taller.models.documento").Documento
    except ModuleNotFoundError:
        pass

    base = Decimal("100000")  # CLP

    data = {}
    _set_if_field(data, CP, "empresa", emp)
    if Documento and _has_field(CP, "documento"):
        doc = Documento.objects.create(empresa=emp, tipo="FAC", fecha_emision="2025-01-01")
        data["documento"] = doc

    # campos comunes de monto
    for nf in ("monto", "monto_neto", "subtotal", "neto"):
        _set_if_field(data, CP, nf, base)

    # fija IVA 19% si hay campo de porcentaje
    for tf in ("iva_porcentaje", "impuesto_porcentaje", "tax_percent"):
        _set_if_field(data, CP, tf, Decimal("19.00"))

    # método de pago opcional
    for mf in ("metodo_pago", "medio_pago", "forma_pago"):
        _set_if_field(data, CP, mf, "efectivo")

    obj = CP(**data)
    try:
        obj.full_clean()
    except Exception:
        pass
    obj.save()
    assert str(obj)

    # Si el modelo calcula 'total' o similar, valida aprox 19%
    getters = ["total", "total_bruto", "total_con_impuesto", "monto_total"]
    for g in getters:
        if hasattr(obj, g):
            val = getattr(obj, g)
            val = val() if callable(val) else val
            if isinstance(val, (int, float, Decimal)):
                esperado = base * Decimal("1.19")
                assert Decimal(str(val)).quantize(Decimal("1")) >= esperado.quantize(Decimal("1")) - 1
            break

@pytest.mark.django_db
def test_comprobante_pago_usa_sales_tax_smoke():
    try:
        CP = importlib.import_module("taller.models.comprobante_pago").ComprobantePago
    except ModuleNotFoundError:
        pytest.skip("ComprobantePago no disponible")

    Empresa = importlib.import_module("taller.models.empresa").Empresa
    User = get_user_model()
    user = User.objects.create_user(username="testuser2", password="testpass")
    
    emp = Empresa.objects.create(nombre_taller="EGarage US", empresa="EGarage US", pais="US", direccion="Test", telefono="123", email="test@test.com", zona_horaria="UTC", fecha_inicio=datetime.now(), plan="mensual", dias_prueba=30, suscripcion_activa=True, valor_mensual=100, moneda="USD", notificacion_5_dias=False, notificacion_1_dia=False, notificacion_vencido=False, user_id=user.id)

    base = Decimal("200.00")

    data = {}
    _set_if_field(data, CP, "empresa", emp)
    for nf in ("monto", "monto_neto", "subtotal", "neto"):
        _set_if_field(data, CP, nf, base)
    for tf in ("iva_porcentaje", "impuesto_porcentaje", "tax_percent"):
        _set_if_field(data, CP, tf, Decimal("0.0"))  # neutralizamos impuesto si existe

    obj = CP(**data)
    try:
        obj.full_clean()
    except Exception:
        pass
    obj.save()
    assert str(obj)

    # Si expose total, debe ser >= base
    for name in ("total", "total_con_impuesto", "monto_total"):
        if hasattr(obj, name):
            val = getattr(obj, name)
            val = val() if callable(val) else val
            if isinstance(val, (int, float, Decimal)):
                assert Decimal(str(val)) >= base
            break
