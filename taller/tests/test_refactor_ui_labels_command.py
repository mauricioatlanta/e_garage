from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from taller.management.commands import refactor_ui_labels


class TestRefactorUiLabelsCommand(SimpleTestCase):
    def _run_command(self, tmp_path: Path, content: str, dry_run: bool = False):
        template_dir = tmp_path / "templates"
        template_dir.mkdir(parents=True)

        template = template_dir / "sample.html"
        template.write_text(content, encoding="utf-8")

        stdout = StringIO()

        with patch.dict(
            refactor_ui_labels.MODULES,
            {"vehiculos": [str(template_dir)]},
            clear=False,
        ):
            call_command(
                "refactor_ui_labels",
                "vehiculos",
                dry_run=dry_run,
                stdout=stdout,
            )

        return template.read_text(encoding="utf-8"), stdout.getvalue()

    def test_reemplaza_texto_html_visible(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result, _ = self._run_command(
                Path(tmp),
                "<label>Patente</label>",
            )

        self.assertEqual(
            result,
            "<label>{{ ui_labels.vehicle_plate }}</label>",
        )

    def test_no_modifica_trans_django(self):
        import tempfile

        source = (
            '{% load i18n %}\n'
            '<label>{% trans "Patente" %}</label>\n'
        )

        with tempfile.TemporaryDirectory() as tmp:
            result, _ = self._run_command(
                Path(tmp),
                source,
            )

        self.assertEqual(result, source)
        self.assertNotIn(
            '{% trans "{{ ui_labels.vehicle_plate }}" %}',
            result,
        )

    def test_no_modifica_otros_trans_django(self):
        import tempfile

        source = (
            '{% load i18n %}\n'
            '{% trans "Cliente" %}\n'
            '{% trans "Vehículo" %}\n'
            '{% trans "Repuesto" %}\n'
            '{% trans "Patente" %}\n'
        )

        with tempfile.TemporaryDirectory() as tmp:
            result, _ = self._run_command(
                Path(tmp),
                source,
            )

        self.assertEqual(result, source)

    def test_dry_run_no_escribe_archivo(self):
        import tempfile

        source = "<label>Patente</label>"

        with tempfile.TemporaryDirectory() as tmp:
            result, stdout = self._run_command(
                Path(tmp),
                source,
                dry_run=True,
            )

        self.assertEqual(result, source)
        self.assertIn("Archivos modificados: 1", stdout)
