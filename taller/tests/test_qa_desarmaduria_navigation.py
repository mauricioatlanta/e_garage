from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from taller.context_processors.qa_control import qa_control


class QaDesarmaduriaNavigationTests(SimpleTestCase):
    class Request:
        user = object()

    def _flag_for(self, context, *, authorized=True):
        with patch(
            "taller.context_processors.qa_control.is_control_tower_user",
            return_value=authorized,
        ), patch(
            "taller.context_processors.qa_control.get_qa_control_context",
            return_value=context,
        ), patch(
            "taller.context_processors.qa_control.resolve_qa_empresa",
            return_value=None,
        ):
            return qa_control(self.Request())["qa_control_is_cl_desarme"]

    def test_cl_desarme_qa_gets_flag(self):
        self.assertTrue(self._flag_for({"country": "CL", "rubro": "DESARMADURIA"}))

    def test_other_country_or_rubro_does_not_get_flag(self):
        self.assertFalse(self._flag_for({"country": "CL", "rubro": "WORKSHOP"}))
        self.assertFalse(self._flag_for({"country": "US", "rubro": "DESARMADURIA"}))

    def test_unauthorized_user_does_not_get_qa_flag(self):
        self.assertFalse(
            self._flag_for({"country": "CL", "rubro": "DESARMADURIA"}, authorized=False)
        )

    def test_base_template_has_isolated_desarmaduria_branch(self):
        template = Path("templates/base.html").read_text()
        self.assertIn('workspace.product_key == "DESARMADURIA"', template)
        self.assertIn("qa_control_is_cl_desarme", template)
