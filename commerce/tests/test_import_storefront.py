"""
Tests del importador de storefront (tests 11-19 del spec):
11. import_storefront --dry-run no escribe.
12. Segunda ejecución es idempotente.
13. Sin --overwrite conserva cambios manuales.
14. Con --overwrite reemplaza campos.
15. Logo se copia al storage de eGarage.
16. Logo ausente deja campo null/intacto.
17. Ningún secreto aparece en logs.
18. manage.py check limpio.
19. makemigrations --check sin cambios.
"""
import io
import json
import os
import tempfile
from pathlib import Path

import pytest
from django.core.management import call_command

from commerce.importers.monteazul import Importer
from commerce.models import (
    CommerceFAQ,
    CommerceStaticPage,
    CommerceStorefrontSettings,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_importer(empresa, **kwargs) -> "ImportResult":
    imp = Importer(empresa, **kwargs)
    return imp.run()


def _make_source_dir(tmp_path: Path, *, with_logo=False, fixture: dict | None = None) -> Path:
    """Crea un directorio que pasa la validación de proyecto MonteAzul."""
    (tmp_path / "manage.py").write_text("# manage")
    (tmp_path / "gestion_taller").mkdir()
    if with_logo:
        media = tmp_path / "media"
        media.mkdir()
        (media / "logomonteazul.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    if fixture is not None:
        (tmp_path / "storefront_data.json").write_text(
            json.dumps(fixture), encoding="utf-8"
        )
    return tmp_path


# ── 11. dry-run no escribe ────────────────────────────────────────────────────

@pytest.mark.django_db
def test_dry_run_writes_nothing(empresa):
    run_importer(empresa, dry_run=True)
    assert not CommerceStorefrontSettings.objects.filter(empresa=empresa).exists()
    assert not CommerceStaticPage.objects.filter(empresa=empresa).exists()
    assert not CommerceFAQ.objects.filter(empresa=empresa).exists()


# ── 12. Idempotencia ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_second_run_is_idempotent(empresa):
    run_importer(empresa)
    count_sf = CommerceStorefrontSettings.objects.filter(empresa=empresa).count()
    count_pg = CommerceStaticPage.objects.filter(empresa=empresa).count()
    count_fq = CommerceFAQ.objects.filter(empresa=empresa).count()

    run_importer(empresa)
    assert CommerceStorefrontSettings.objects.filter(empresa=empresa).count() == count_sf
    assert CommerceStaticPage.objects.filter(empresa=empresa).count() == count_pg
    assert CommerceFAQ.objects.filter(empresa=empresa).count() == count_fq


# ── 13. Sin --overwrite conserva cambios manuales ────────────────────────────

@pytest.mark.django_db
def test_without_overwrite_preserves_manual_changes(empresa):
    run_importer(empresa)
    sf = CommerceStorefrontSettings.objects.get(empresa=empresa)
    sf.tagline = "Edición manual"
    sf.save()

    run_importer(empresa, overwrite=False)
    sf.refresh_from_db()
    assert sf.tagline == "Edición manual"


# ── 14. Con --overwrite reemplaza campos ──────────────────────────────────────

@pytest.mark.django_db
def test_overwrite_replaces_fields(empresa):
    run_importer(empresa)
    sf = CommerceStorefrontSettings.objects.get(empresa=empresa)
    sf.tagline = "Edición manual"
    sf.save()

    run_importer(empresa, overwrite=True)
    sf.refresh_from_db()
    assert sf.tagline != "Edición manual"


# ── 15. Logo se copia al storage ─────────────────────────────────────────────

@pytest.mark.django_db
def test_logo_copied_to_storage(empresa, tmp_path):
    src = _make_source_dir(tmp_path, with_logo=True)
    result = run_importer(empresa, source=str(src))
    assert result.logo_copied
    sf = CommerceStorefrontSettings.objects.get(empresa=empresa)
    assert sf.logo  # campo no vacío


# ── 16. Logo ausente deja campo null ─────────────────────────────────────────

@pytest.mark.django_db
def test_missing_logo_leaves_field_null(empresa, tmp_path):
    src = _make_source_dir(tmp_path, with_logo=False)
    result = run_importer(empresa, source=str(src))
    assert not result.logo_copied
    sf = CommerceStorefrontSettings.objects.get(empresa=empresa)
    assert not sf.logo


# ── 17. Ningún secreto aparece en resultado ───────────────────────────────────

@pytest.mark.django_db
def test_no_secrets_in_output(empresa, tmp_path, capsys):
    src = _make_source_dir(tmp_path)
    run_importer(empresa, source=str(src), dry_run=True)
    captured = capsys.readouterr()
    for secret_keyword in ["SECRET_KEY", "password", "WEBPAY", "API_KEY"]:
        assert secret_keyword.lower() not in captured.out.lower()
        assert secret_keyword.lower() not in captured.err.lower()


# ── 18. manage.py check limpio ───────────────────────────────────────────────

@pytest.mark.django_db
def test_manage_check_passes():
    out = io.StringIO()
    call_command("check", stdout=out, stderr=out)
    assert "no issues" in out.getvalue().lower()


# ── 19. makemigrations --check sin cambios ───────────────────────────────────

@pytest.mark.django_db
def test_no_pending_migrations():
    out = io.StringIO()
    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=out, stderr=out)
    except SystemExit as exc:
        # makemigrations --check exits 1 cuando hay cambios pendientes
        assert exc.code == 0, f"Hay migraciones pendientes:\n{out.getvalue()}"
