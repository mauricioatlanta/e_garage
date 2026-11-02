"""
Tests del MediaResolver.

Verifica los tres casos de resolución (found / missing / ambiguous),
el glob recursivo en subdirectorios, el fallback por ruta completa,
y la generación correcta de manual_review.json.
"""
import json

import pytest

from commerce.services.catalog.media_resolver import MediaResolver


# ── Fixtures de sistema de archivos ──────────────────────────────────────────

@pytest.fixture
def media_root(tmp_path):
    """Árbol de archivos simulado en tmp_path."""
    root = tmp_path / "media"
    (root / "productos" / "2026" / "01").mkdir(parents=True)
    (root / "productos" / "2026" / "02").mkdir(parents=True)
    (root / "productos" / "2026" / "01" / "filtro.jpg").write_bytes(b"\xff" * 10)
    (root / "productos" / "2026" / "02" / "aceite.png").write_bytes(b"\xff" * 10)
    # Archivo duplicado (mismo nombre en dos subdirectorios → ambiguo)
    (root / "productos" / "2026" / "01" / "dup.jpg").write_bytes(b"\x01" * 10)
    (root / "productos" / "2026" / "02" / "dup.jpg").write_bytes(b"\x02" * 10)
    return root


def _resolver(media_root, search_dirs=("productos",)):
    return MediaResolver(media_root, search_dirs)


# ── Casos de resolución ───────────────────────────────────────────────────────

def test_resolve_finds_file_in_search_dir(media_root):
    r = _resolver(media_root)
    path = r.resolve("products/2026/02/aceite.png")

    assert path is not None
    assert path.name == "aceite.png"
    assert not r.has_issues


def test_resolve_finds_file_in_subdirectory(media_root):
    r = _resolver(media_root)
    path = r.resolve("products/X/Y/filtro.jpg")

    assert path is not None
    assert path.name == "filtro.jpg"
    assert not r.has_issues


def test_resolve_returns_none_when_missing(media_root):
    r = _resolver(media_root)
    path = r.resolve("products/2026/03/noexiste.jpg")

    assert path is None
    assert r.missing_count == 1
    assert r.has_issues
    assert "products/2026/03/noexiste.jpg" in r.missing


def test_resolve_ambiguous_returns_first_sorted(media_root):
    r = _resolver(media_root)
    path = r.resolve("products/2026/X/dup.jpg")

    assert path is not None
    assert path.name == "dup.jpg"
    assert r.ambiguous_count == 1
    assert r.has_issues

    record = r.ambiguous[0]
    assert record["db_path"] == "products/2026/X/dup.jpg"
    # Candidatos ordenados lexicográficamente
    assert record["candidates"][0] < record["candidates"][1]
    assert str(path) == record["candidates"][0]


def test_resolve_fallback_to_full_path(tmp_path):
    """Si no hay coincidencias en search_dirs, usa la ruta completa bajo media_root."""
    root = tmp_path / "media"
    exact = root / "products" / "2026" / "02" / "archivo.jpg"
    exact.parent.mkdir(parents=True)
    exact.write_bytes(b"\xff" * 10)

    r = MediaResolver(root, search_dirs=())  # sin search_dirs
    path = r.resolve("products/2026/02/archivo.jpg")

    assert path == exact
    assert not r.has_issues


def test_resolve_empty_db_path_returns_none(media_root):
    r = _resolver(media_root)
    path = r.resolve("")

    assert path is None
    assert r.missing_count == 1


def test_resolve_multiple_search_dirs(tmp_path):
    """Archivo en el segundo search_dir pero no en el primero → encontrado sin ambigüedad."""
    root = tmp_path / "media"
    (root / "fotos" / "sub").mkdir(parents=True)
    (root / "imagenes" / "sub").mkdir(parents=True)
    # img.jpg solo en "imagenes", no en "fotos" → un único candidato
    (root / "imagenes" / "sub" / "img.jpg").write_bytes(b"\x02")

    r = MediaResolver(root, search_dirs=("fotos", "imagenes"))
    path = r.resolve("products/img.jpg")

    assert path is not None
    assert "imagenes" in str(path)
    assert not r.has_issues


def test_resolve_accumulates_multiple_calls(media_root):
    r = _resolver(media_root)
    r.resolve("products/noexiste1.jpg")
    r.resolve("products/noexiste2.jpg")

    assert r.missing_count == 2
    assert len(r.missing) == 2


# ── has_issues ────────────────────────────────────────────────────────────────

def test_has_issues_false_when_no_calls(media_root):
    r = _resolver(media_root)
    assert not r.has_issues
    assert r.missing_count == 0
    assert r.ambiguous_count == 0


def test_has_issues_true_after_missing(media_root):
    r = _resolver(media_root)
    r.resolve("products/X/noexiste.jpg")
    assert r.has_issues


def test_has_issues_true_after_ambiguous(media_root):
    r = _resolver(media_root)
    r.resolve("products/X/dup.jpg")
    assert r.has_issues


def test_has_issues_false_when_all_found(media_root):
    r = _resolver(media_root)
    r.resolve("products/X/filtro.jpg")
    r.resolve("products/Y/aceite.png")
    assert not r.has_issues


# ── write_review_if_needed ────────────────────────────────────────────────────

def test_write_review_skips_when_no_issues(media_root, tmp_path):
    r = _resolver(media_root)
    r.resolve("products/filtro.jpg")  # found → no issue

    out = tmp_path / "review.json"
    written = r.write_review_if_needed(out)

    assert written is False
    assert not out.exists()


def test_write_review_creates_json_when_missing(media_root, tmp_path):
    r = _resolver(media_root)
    r.resolve("products/noexiste.jpg")

    out = tmp_path / "review.json"
    written = r.write_review_if_needed(out, empresa_id=28)

    assert written is True
    assert out.exists()

    data = json.loads(out.read_text())
    assert data["empresa_id"] == 28
    assert data["summary"]["missing"] == 1
    assert data["summary"]["ambiguous"] == 0
    assert "products/noexiste.jpg" in data["missing"]
    assert data["ambiguous"] == []


def test_write_review_creates_json_when_ambiguous(media_root, tmp_path):
    r = _resolver(media_root)
    r.resolve("products/dup.jpg")

    out = tmp_path / "review.json"
    written = r.write_review_if_needed(out)

    assert written is True
    data = json.loads(out.read_text())
    assert data["summary"]["ambiguous"] == 1
    assert data["summary"]["missing"] == 0
    assert len(data["ambiguous"]) == 1
    assert data["ambiguous"][0]["db_path"] == "products/dup.jpg"
    assert len(data["ambiguous"][0]["candidates"]) == 2


def test_write_review_json_has_generated_at(media_root, tmp_path):
    r = _resolver(media_root)
    r.resolve("products/noexiste.jpg")

    out = tmp_path / "review.json"
    r.write_review_if_needed(out)

    data = json.loads(out.read_text())
    assert "generated_at" in data
    assert "T" in data["generated_at"]  # ISO 8601


def test_write_review_overwrites_existing_file(media_root, tmp_path):
    out = tmp_path / "review.json"
    out.write_text('{"stale": true}')

    r = _resolver(media_root)
    r.resolve("products/noexiste.jpg")
    r.write_review_if_needed(out)

    data = json.loads(out.read_text())
    assert "stale" not in data
    assert "summary" in data


def test_write_review_json_is_utf8_valid(media_root, tmp_path):
    r = _resolver(media_root)
    r._missing.append("products/ñoño/archivo.jpg")

    out = tmp_path / "review.json"
    r.write_review_if_needed(out)

    text = out.read_text(encoding="utf-8")
    assert "ñoño" in text
