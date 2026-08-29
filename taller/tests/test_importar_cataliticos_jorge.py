import hashlib
import json
from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

from taller.management.commands.importar_cataliticos_jorge import EXPECTED_CODES
from taller.models.reciclaje import Catalitico
from taller.tests.factories import EmpresaFactory


PRICES = {
    "Y1": 64000,
    "UDX011": 83000,
    "K564": 76000,
    "K208": 40000,
    "K357": 90000,
    "F0C": 60000,
    "C137": 51000,
    "K181": 57000,
    "5QM178AA": 7000,
    "2QB": 40000,
    "8K0131701S": 72000,
    "NA3": 61000,
    "79GC02": 19000,
    "K179": 35000,
    "T16": 45000,
    "25129125": 61000,
    "BG": 123000,
    "8X": 53000,
    "M8": 51000,
    "T24": 79000,
    "W2BS1": 45000,
    "K212": 10000,
    "K130": 10000,
}

EXISTING = {
    "K208": ("26746.50", "67000.00"),
    "K357": ("49035.25", "129300.00"),
    "C137": ("25000.00", "86100.00"),
    "K181": ("35662.00", "74400.00"),
    "NA3": ("31204.25", "79000.00"),
    "25129125": ("22288.75", "93000.00"),
    "M8": ("31204.25", "74700.00"),
}


@pytest.fixture
def atlanta(db):
    user = User.objects.create_user(
        username="atlanta_import_test",
        email="atlanta-import@example.com",
        password="pass1234",
    )
    return EmpresaFactory(
        user=user,
        nombre_taller="Atlanta Reciclajes",
        pais="CL",
    )


@pytest.fixture
def source_json(tmp_path):
    assert set(PRICES) == set(EXPECTED_CODES)

    rows = []

    for code, price in PRICES.items():
        rows.append(
            {
                "code": code,
                "normalized_code": code,
                "price_jorge": f"{price:.2f}",
                "purchase_suggestion": f"{price / 2:.2f}",
                "action": (
                    "ACTUALIZAR_VALOR_VENTA"
                    if code in EXISTING
                    else "CREAR_CATALITICO"
                ),
                "status": (
                    "EXISTENTE_CON_ACTUALIZACION"
                    if code in EXISTING
                    else "NUEVO"
                ),
                "new_values": (
                    {"valor_venta": f"{price:.2f}"}
                    if code in EXISTING
                    else {
                        "precio_referencia_original": f"{price:.2f}",
                        "valor_compra_sugerido": f"{price / 2:.2f}",
                        "valor_venta": f"{price:.2f}",
                    }
                ),
            }
        )

    path = tmp_path / "jorge_confirmed.json"
    raw = json.dumps(
        {"final_confirmed": rows},
        sort_keys=True,
    ).encode()

    path.write_bytes(raw)

    return path, hashlib.sha256(raw).hexdigest()


def create_existing(atlanta):
    created = {}

    for code, (compra, venta) in EXISTING.items():
        created[code] = Catalitico.objects.create(
            empresa=atlanta,
            codigo=code,
            nombre="Existente",
            precio_compra=Decimal(compra),
            precio_venta=Decimal(venta),
            cantidad_stock=1,
            estado=Catalitico.ESTADO_DISPONIBLE,
            activo=True,
        )

    return created


@pytest.mark.django_db
def test_dry_run_no_escribe(atlanta, source_json):
    create_existing(atlanta)

    before = {
        c.codigo: (
            c.precio_compra,
            c.precio_venta,
        )
        for c in Catalitico.objects.filter(empresa=atlanta)
    }

    path, sha = source_json
    out = StringIO()

    call_command(
        "importar_cataliticos_jorge",
        str(path),
        empresa_id=atlanta.pk,
        expected_sha256=sha,
        stdout=out,
    )

    text = out.getvalue()

    assert "CREATE=16" in text
    assert "UPDATE=7" in text
    assert "TOTAL=23" in text
    assert "MODE=DRY_RUN" in text
    assert "WRITES=0" in text

    after = {
        c.codigo: (
            c.precio_compra,
            c.precio_venta,
        )
        for c in Catalitico.objects.filter(empresa=atlanta)
    }

    assert after == before
    assert Catalitico.objects.filter(empresa=atlanta).count() == 7


@pytest.mark.django_db
def test_dry_run_plan_produccion_16_create_7_update_sin_escribir(
    atlanta,
    source_json,
):
    create_existing(atlanta)
    before = {
        c.codigo: (c.precio_compra, c.precio_venta)
        for c in Catalitico.objects.filter(empresa=atlanta)
    }

    path, sha = source_json
    out = StringIO()

    call_command(
        "importar_cataliticos_jorge",
        str(path),
        empresa_id=atlanta.pk,
        expected_sha256=sha,
        stdout=out,
    )

    text = out.getvalue()

    assert "CREATE=16" in text
    assert "UPDATE=7" in text
    assert "TOTAL=23" in text
    assert "MODE=DRY_RUN" in text
    assert "WRITES=0" in text

    assert Catalitico.objects.filter(empresa=atlanta).count() == 7

    after = {
        c.codigo: (c.precio_compra, c.precio_venta)
        for c in Catalitico.objects.filter(empresa=atlanta)
    }

    assert after == before


@pytest.mark.django_db
def test_apply_crea_16_y_actualiza_7_preservando_precio_compra(
    atlanta,
    source_json,
):
    create_existing(atlanta)

    compras_originales = {
        c.codigo: c.precio_compra
        for c in Catalitico.objects.filter(empresa=atlanta)
    }

    path, sha = source_json
    out = StringIO()

    call_command(
        "importar_cataliticos_jorge",
        str(path),
        empresa_id=atlanta.pk,
        expected_sha256=sha,
        apply=True,
        stdout=out,
    )

    text = out.getvalue()

    assert "CREATE=16" in text
    assert "UPDATE=7" in text
    assert "TOTAL=23" in text
    assert "MODE=APPLY" in text
    assert "WRITES=23" in text
    assert "APPLY_OK=1" in text

    qs = Catalitico.objects.filter(empresa=atlanta)
    assert qs.count() == 23

    for code, compra_original in compras_originales.items():
        cat = qs.get(codigo=code)

        assert cat.precio_compra == compra_original
        assert cat.precio_venta == Decimal(f"{PRICES[code]:.2f}")

    for code, price in PRICES.items():
        if code in EXISTING:
            continue

        cat = qs.get(codigo=code)

        expected_venta = Decimal(f"{price:.2f}")
        expected_compra = expected_venta * Decimal("0.50")

        assert cat.precio_venta == expected_venta
        assert cat.precio_compra == expected_compra


@pytest.mark.django_db
def test_sha_incorrecto_aborta_sin_escribir(atlanta, source_json):
    path, _sha = source_json

    with pytest.raises(CommandError, match="SHA256_NO_COINCIDE"):
        call_command(
            "importar_cataliticos_jorge",
            str(path),
            empresa_id=atlanta.pk,
            expected_sha256="0" * 64,
        )

    assert Catalitico.objects.filter(empresa=atlanta).count() == 0


@pytest.mark.django_db
def test_rechaza_tenant_que_no_es_atlanta(atlanta, source_json):
    atlanta.nombre_taller = "Empresa Incorrecta"
    atlanta.save(update_fields=["nombre_taller"])

    path, sha = source_json

    with pytest.raises(CommandError, match="EMPRESA_NO_PARECE_ATLANTA"):
        call_command(
            "importar_cataliticos_jorge",
            str(path),
            empresa_id=atlanta.pk,
            expected_sha256=sha,
        )

    assert Catalitico.objects.filter(empresa=atlanta).count() == 0


@pytest.mark.django_db
def test_aborta_si_fuente_dice_nuevo_pero_codigo_ya_existe(
    atlanta,
    source_json,
):
    Catalitico.objects.create(
        empresa=atlanta,
        codigo="Y1",
        nombre="Apareció antes del import",
        precio_compra=Decimal("11111.00"),
        precio_venta=Decimal("22222.00"),
        cantidad_stock=1,
        estado=Catalitico.ESTADO_DISPONIBLE,
        activo=True,
    )

    path, sha = source_json

    with pytest.raises(
        CommandError,
        match="CONTRATO_FUENTE_BD_NO_COINCIDE",
    ):
        call_command(
            "importar_cataliticos_jorge",
            str(path),
            empresa_id=atlanta.pk,
            expected_sha256=sha,
        )

    cat = Catalitico.objects.get(
        empresa=atlanta,
        codigo="Y1",
    )

    assert cat.precio_compra == Decimal("11111.00")
    assert cat.precio_venta == Decimal("22222.00")
