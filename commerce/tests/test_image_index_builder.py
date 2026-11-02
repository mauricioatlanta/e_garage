"""
Tests de ImageIndexBuilder y del modo índice de MediaResolver.
"""
import json

import pytest

from commerce.services.catalog.image_index import ImageIndexBuilder
from commerce.services.catalog.media_resolver import MediaResolver


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def image_tree(tmp_path):
    """
    Árbol simulado de imágenes en múltiples subdirectorios.

    media/productos/SILENCIADORES/LT043.png
    media/productos/FLEXIBLES/DW002.jpg
    media/productos/CATALITICOS/CAT001.png
    imagenes/catalogo/CAT001.png          ← mismo nombre que CAT001.png → ambiguo
    imagenes/archivos/LT043.PNG           ← case variant → mismo key que LT043.png
    """
    root1 = tmp_path / "media" / "productos"
    (root1 / "SILENCIADORES").mkdir(parents=True)
    (root1 / "FLEXIBLES").mkdir(parents=True)
    (root1 / "CATALITICOS").mkdir(parents=True)
    (root1 / "SILENCIADORES" / "LT043.png").write_bytes(b"\x01" * 10)
    (root1 / "FLEXIBLES" / "DW002.jpg").write_bytes(b"\x02" * 10)
    (root1 / "CATALITICOS" / "CAT001.png").write_bytes(b"\x03" * 10)

    root2 = tmp_path / "imagenes"
    (root2 / "catalogo").mkdir(parents=True)
    (root2 / "archivos").mkdir(parents=True)
    (root2 / "catalogo" / "CAT001.png").write_bytes(b"\x04" * 10)
    (root2 / "archivos" / "LT043.PNG").write_bytes(b"\x05" * 10)

    return tmp_path, root1.parent, root2


# ── ImageIndexBuilder ─────────────────────────────────────────────────────────

def test_build_creates_output_file(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "idx" / "image_index.json"
    builder = ImageIndexBuilder([root1, root2], out)
    builder.build()
    assert out.exists()


def test_build_index_contains_all_unique_names(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "image_index.json"
    builder = ImageIndexBuilder([root1, root2], out)
    index = builder.build()
    assert "lt043.png" in index
    assert "dw002.jpg" in index
    assert "cat001.png" in index


def test_build_case_insensitive_key(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "image_index.json"
    builder = ImageIndexBuilder([root1, root2], out)
    index = builder.build()
    # LT043.png y LT043.PNG deben colapsar al mismo key
    assert len(index["lt043.png"]) == 2


def test_build_ambiguous_names_have_multiple_paths(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "image_index.json"
    builder = ImageIndexBuilder([root1, root2], out)
    index = builder.build()
    assert len(index["cat001.png"]) == 2


def test_build_paths_are_sorted(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "image_index.json"
    builder = ImageIndexBuilder([root1, root2], out)
    index = builder.build()
    for paths in index.values():
        assert paths == sorted(paths)


def test_build_json_has_meta(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "image_index.json"
    ImageIndexBuilder([root1, root2], out).build()
    data = json.loads(out.read_text())
    assert "_meta" in data
    assert data["_meta"]["total_files"] == 5
    assert data["_meta"]["ambiguous_names"] == 2  # cat001.png, lt043.png


def test_build_ignores_non_image_files(tmp_path):
    root = tmp_path / "mixed"
    root.mkdir()
    (root / "archivo.txt").write_bytes(b"texto")
    (root / "readme.md").write_bytes(b"docs")
    (root / "foto.jpg").write_bytes(b"\xff\xd8")
    out = tmp_path / "index.json"
    index = ImageIndexBuilder([root], out).build()
    assert "foto.jpg" in index
    assert "archivo.txt" not in index
    assert "readme.md" not in index


def test_build_skips_nonexistent_root(tmp_path):
    out = tmp_path / "index.json"
    index = ImageIndexBuilder([tmp_path / "no_existe"], out).build()
    assert index == {}


def test_load_reads_index_section(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "image_index.json"
    ImageIndexBuilder([root1, root2], out).build()
    loaded = ImageIndexBuilder.load(out)
    assert "lt043.png" in loaded
    assert isinstance(loaded["lt043.png"], list)


def test_stats_returns_correct_counts(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "image_index.json"
    index = ImageIndexBuilder([root1, root2], out).build()
    stats = ImageIndexBuilder.stats(index)
    assert stats["total_files"] == 5
    assert stats["unique_names"] == 3
    assert stats["ambiguous_names"] == 2


# ── MediaResolver modo índice ─────────────────────────────────────────────────

@pytest.fixture
def index_file(image_tree, tmp_path):
    _, root1, root2 = image_tree
    out = tmp_path / "image_index.json"
    ImageIndexBuilder([root1, root2], out).build()
    return out


def test_resolver_with_index_finds_unique(index_file, tmp_path):
    r = MediaResolver(tmp_path / "media", index_path=index_file)
    path = r.resolve("products/2026/02/02/DW002.jpg")
    assert path is not None
    assert path.name == "DW002.jpg"
    assert not r.has_issues


def test_resolver_with_index_case_insensitive(index_file, tmp_path):
    # DB guarda "LT043.png", índice tiene key "lt043.png" con dos rutas
    r = MediaResolver(tmp_path / "media", index_path=index_file)
    path = r.resolve("products/2026/02/02/LT043.png")
    assert path is not None
    assert path.name.lower() == "lt043.png"
    # Dos candidatos → ambiguo
    assert r.ambiguous_count == 1


def test_resolver_with_index_reports_missing(index_file, tmp_path):
    r = MediaResolver(tmp_path / "media", index_path=index_file)
    path = r.resolve("products/NOEXISTE.png")
    assert path is None
    assert r.missing_count == 1


def test_resolver_with_index_ambiguous_returns_first_sorted(index_file, tmp_path):
    r = MediaResolver(tmp_path / "media", index_path=index_file)
    path = r.resolve("old/CAT001.png")
    assert path is not None
    record = r.ambiguous[0]
    assert str(path) == record["candidates"][0]
    assert record["candidates"] == sorted(record["candidates"])


def test_resolver_without_index_still_uses_glob(tmp_path):
    """El modo glob original no se rompe."""
    root = tmp_path / "media"
    (root / "productos" / "sub").mkdir(parents=True)
    (root / "productos" / "sub" / "pieza.jpg").write_bytes(b"\xff")
    r = MediaResolver(root, search_dirs=("productos",))
    path = r.resolve("old/pieza.jpg")
    assert path is not None
    assert path.name == "pieza.jpg"
    assert not r.has_issues


def test_resolver_index_path_not_found_falls_back_to_glob(tmp_path):
    """Si index_path no existe, usa glob silenciosamente."""
    root = tmp_path / "media"
    (root / "productos").mkdir(parents=True)
    (root / "productos" / "x.jpg").write_bytes(b"\xff")
    nonexistent_index = tmp_path / "no_index.json"
    r = MediaResolver(root, search_dirs=("productos",), index_path=nonexistent_index)
    path = r.resolve("x.jpg")
    assert path is not None
