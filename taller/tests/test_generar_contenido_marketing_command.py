"""
Tests para el management command generar_contenido_marketing.

Cubre:
  - creación de archivos con estructura correcta
  - protección contra sobrescritura sin --force
  - --force sobreescribe carpeta existente
  - --dry-run no crea archivos
  - sanitización del slug en nombre de carpeta
  - ausencia de PII en los archivos generados
  - JSON de paquete es parseable y tiene campos requeridos
"""
import json
import re
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from taller.services.marketing_content_service import (
    FORMAT_VERSION,
    MarketingPackage,
    slugify,
)
from datetime import date

FEATURE     = "Briefing inteligente para desarmadurías"
DESCRIPCION = "Panel que analiza indicadores del negocio y entrega alertas, resumen y recomendaciones"
FAKE_DATE   = date(2026, 8, 4)

_EXPECTED_FILES = {
    "facebook.md",
    "instagram.md",
    "tiktok.md",
    "reel_guion.md",
    "historias.md",
    "hashtags.md",
    "paquete.json",
}


def _make_fake_package(**kwargs) -> MarketingPackage:
    defaults = dict(
        feature=FEATURE,
        descripcion=DESCRIPCION,
        fecha=FAKE_DATE,
        idioma="es",
        publico_objetivo="Talleres en Latinoamérica",
        pais="CL",
        propuesta_valor="Gestión inteligente",
        facebook={"texto": "Texto de Facebook profesional y cercano. egarage.cl"},
        instagram={"texto": "⚡ Texto breve Instagram 👉 egarage.cl"},
        tiktok={
            "gancho": "¿Tu taller sin briefing inteligente?",
            "guion":  "Guion TikTok completo aquí.",
            "texto_pantalla": ["NUEVO", "eGarage", "egarage.cl"],
            "escenas": ["escena 1: dashboard", "escena 2: celular", "escena 3: logo"],
            "cta": "Empieza gratis en egarage.cl",
        },
        reel={
            "escenas": [
                {"tiempo": "0-5s",  "texto": "¿Cómo va tu negocio?", "visual": "pantalla dashboard"},
                {"tiempo": "5-12s", "texto": "Briefing inteligente",  "visual": "animación KPIs"},
                {"tiempo": "12-20s","texto": "Todo en un panel",      "visual": "vista general"},
                {"tiempo": "20-27s","texto": "egarage.cl",            "visual": "logo eGarage"},
            ]
        },
        historias=[
            {"pantalla": 1, "texto": "⚡ Nuevo en eGarage", "cta": False},
            {"pantalla": 2, "texto": FEATURE, "cta": False},
            {"pantalla": 3, "texto": "Alertas y recomendaciones", "cta": False},
            {"pantalla": 4, "texto": "Disponible ahora", "cta": False},
            {"pantalla": 5, "texto": "Pruébalo gratis en egarage.cl", "cta": True},
        ],
        hashtags=["eGarage", "TallerMecanico", "Desarmaduria"],
        fallback_used=True,
        modelo="",
    )
    defaults.update(kwargs)
    return MarketingPackage(**defaults)


def _call_command_with_dest(dest: Path, *extra_args, **extra_kwargs) -> StringIO:
    """Llama al command redirigiendo _MARKETING_ROOT al directorio temporal."""
    stdout = StringIO()
    with patch(
        "taller.management.commands.generar_contenido_marketing._MARKETING_ROOT",
        dest,
    ):
        with patch(
            "taller.management.commands.generar_contenido_marketing.MarketingContentService.generate",
            return_value=_make_fake_package(),
        ):
            call_command(
                "generar_contenido_marketing",
                feature=FEATURE,
                descripcion=DESCRIPCION,
                stdout=stdout,
                *extra_args,
                **extra_kwargs,
            )
    return stdout


class TestCommandFileCreation(TestCase):

    def test_creates_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            _call_command_with_dest(dest)
            created = {p.name for p in dest.iterdir() if p.is_dir()}
            assert len(created) == 1
            folder = dest / list(created)[0]
            files = {p.name for p in folder.iterdir()}
            assert files == _EXPECTED_FILES

    def test_folder_name_contains_date_and_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            with patch(
                "taller.management.commands.generar_contenido_marketing._MARKETING_ROOT", dest
            ):
                with patch(
                    "taller.management.commands.generar_contenido_marketing.MarketingContentService.generate",
                    return_value=_make_fake_package(),
                ):
                    with patch(
                        "taller.management.commands.generar_contenido_marketing.date"
                    ) as mock_date:
                        mock_date.today.return_value = FAKE_DATE
                        call_command("generar_contenido_marketing", feature=FEATURE, descripcion=DESCRIPCION)

            folders = list(dest.iterdir())
            assert len(folders) == 1
            name = folders[0].name
            assert name.startswith("2026-08-04-")
            assert "briefing" in name or "inteligente" in name

    def test_paquete_json_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            _call_command_with_dest(dest)
            folder = list(dest.iterdir())[0]
            data = json.loads((folder / "paquete.json").read_text())
            assert data["formato_version"] == FORMAT_VERSION
            assert data["feature"] == FEATURE
            assert "redes" in data
            assert "hashtags" in data

    def test_facebook_md_contains_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            _call_command_with_dest(dest)
            folder = list(dest.iterdir())[0]
            content = (folder / "facebook.md").read_text()
            assert "egarage.cl" in content

    def test_reel_guion_md_has_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            _call_command_with_dest(dest)
            folder = list(dest.iterdir())[0]
            content = (folder / "reel_guion.md").read_text()
            assert "|" in content   # tabla markdown

    def test_no_pii_in_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            _call_command_with_dest(dest)
            folder = list(dest.iterdir())[0]
            all_text = ""
            for f in folder.iterdir():
                all_text += f.read_text()
            assert not re.search(r"\d{2}\.\d{3}\.\d{3}-[\dkK]", all_text)  # RUT
            assert not re.search(r"\+56\d{9}", all_text)                     # teléfono CL


class TestCommandOverwriteProtection(TestCase):

    def test_fails_if_folder_exists_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            _call_command_with_dest(dest)  # primera ejecución
            with pytest.raises(CommandError, match="ya existe|--force"):
                _call_command_with_dest(dest)  # segunda sin --force

    def test_force_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            _call_command_with_dest(dest)
            # Segunda ejecución con --force no debe lanzar error
            _call_command_with_dest(dest, force=True)
            folders = list(dest.iterdir())
            assert len(folders) == 1  # misma carpeta, no duplicada


class TestCommandDryRun(TestCase):

    def test_dry_run_creates_no_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            _call_command_with_dest(dest, dry_run=True)
            assert list(dest.iterdir()) == []

    def test_dry_run_prints_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            stdout = _call_command_with_dest(dest, dry_run=True)
            output = stdout.getvalue()
            assert "DRY-RUN" in output


class TestCommandSlugSanitization(TestCase):

    def test_special_chars_in_feature_produce_safe_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            with patch(
                "taller.management.commands.generar_contenido_marketing._MARKETING_ROOT", dest
            ):
                with patch(
                    "taller.management.commands.generar_contenido_marketing.MarketingContentService.generate",
                    return_value=_make_fake_package(),
                ):
                    call_command(
                        "generar_contenido_marketing",
                        feature="Feature con (paréntesis) y ñ!",
                        descripcion=DESCRIPCION,
                    )
            folders = list(dest.iterdir())
            assert len(folders) == 1
            folder_name = folders[0].name
            # No debe contener chars peligrosos para FS
            assert "(" not in folder_name
            assert ")" not in folder_name
            assert "!" not in folder_name

    def test_slug_max_length_respected(self):
        long_feature = "Una funcionalidad con un nombre extremadamente largo que supera el límite máximo permitido por el sistema"
        slug = slugify(long_feature)
        assert len(slug) <= 50
