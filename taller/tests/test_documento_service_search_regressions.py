from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from taller.models.empresa import Empresa
from taller.servicios.models import CategoriaServicio, Servicio


class TestDocumentoServiceSearchRegressions(TestCase):
    def test_documento_form_redirects_to_country_aware_login_when_anonymous(self):
        response = self.client.get("/cl/es/documentos/form/", follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["Location"],
            "/cl/es/accounts/login/?next=/cl/es/documentos/form/",
        )

    def test_busqueda_siembra_servicios_para_empresa_sin_catalogo(self):
        fuente_user = User.objects.create_user(username="fuente_srv", password="123")
        empresa_fuente = Empresa.objects.create(
            user=fuente_user,
            nombre_taller="Fuente CL",
            pais="CL",
            moneda="CLP",
        )
        destino_user = User.objects.create_user(username="destino_srv", password="123")
        empresa_destino = Empresa.objects.create(
            user=destino_user,
            nombre_taller="Destino CL",
            pais="CL",
            moneda="CLP",
        )

        categoria = CategoriaServicio.objects.create(country="CL", code="MANT")
        Servicio.objects.create(
            nombre="Cambio de aceite",
            empresa=empresa_fuente,
            categoria=categoria,
            precio_base=25000,
            activo=True,
        )

        self.client.force_login(destino_user)
        response = self.client.get("/cl/es/documentos/api/buscar-servicios/", {"q": "aceite"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["servicios"][0]["nombre"], "Cambio de aceite")
        self.assertTrue(
            Servicio.objects.filter(
                empresa=empresa_destino,
                nombre="Cambio de aceite",
                categoria=categoria,
            ).exists()
        )

    def test_documento_form_prefetch_no_depende_de_servicio_name(self):
        user = User.objects.create_user(username="prefetch_srv", password="123")
        empresa = Empresa.objects.create(
            user=user,
            nombre_taller="Prefetch CL",
            pais="CL",
            moneda="CLP",
        )
        categoria = CategoriaServicio.objects.create(country="CL", code="MANT")
        Servicio.objects.create(
            nombre="Revision de frenos",
            empresa=empresa,
            categoria=categoria,
            precio_base=22000,
            activo=True,
        )

        self.client.force_login(user)
        response = self.client.get("/cl/es/documentos/form/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('id="prefetchServicios"', content)
        self.assertIn("Revision de frenos", content)

    def test_documento_form_services_table_uses_unique_rows_without_qty_column(self):
        user = User.objects.create_user(username="unique_srv", password="123")
        Empresa.objects.create(
            user=user,
            nombre_taller="Servicios Unicos CL",
            pais="CL",
            moneda="CLP",
        )

        self.client.force_login(user)
        response = self.client.get("/cl/es/documentos/form/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        services_block = content.split(
            '<table class="doc-sheet-table doc-sheet-table-servicios">', 1
        )[1].split("</table>", 1)[0]

        self.assertNotIn("doc-col-qty", services_block)
        self.assertIn('colspan="5"', services_block)

        servicios_js = (
            Path(settings.BASE_DIR) / "static" / "js" / "document-form" / "servicios.js"
        ).read_text(encoding="utf-8")
        self.assertNotIn("serv-cantidad", servicios_js)
