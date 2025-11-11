from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from taller.servicios.models import Servicio


class TestApiBuscarServicios(TestCase):
    def test_api_buscar_servicios_filtra_y_retorna_json(self):
        """
        Verifica que:
          1. Devuelva 200 con resultados JSON.
          2. Solo liste servicios de la empresa del usuario.
          3. Filtre inteligentemente por nombre/código.
        """

        # --- Setup: usuario + empresa ---
        user = User.objects.create_user(username="tester", password="123")
        empresa = getattr(user, "empresa", None)
        if not empresa:
            from taller.models.empresa import Empresa

            empresa = Empresa.objects.create(
                user=user, nombre_taller="Demo Co", pais="US", moneda="USD"
            )

        # --- Crear categorías necesarias ---
        from taller.servicios.models import CategoriaServicio

        categoria = CategoriaServicio.objects.create(country="US", code="MAINT")

        # --- Crea servicios de la empresa del usuario ---
        Servicio.objects.create(nombre="Oil Change", empresa=empresa, categoria=categoria)
        Servicio.objects.create(nombre="Brake Service", empresa=empresa, categoria=categoria)
        Servicio.objects.create(nombre="Air Filter", empresa=empresa, categoria=categoria)

        # --- Servicio de otra empresa (no debería aparecer) ---
        from taller.models.empresa import Empresa

        otra_user = User.objects.create_user(username="otro", password="123")
        otra = Empresa.objects.create(user=otra_user, nombre_taller="Otra", pais="CL", moneda="CLP")
        Servicio.objects.create(nombre="Tire Change", empresa=otra, categoria=categoria)

        self.client.force_login(user)

        url = reverse("documentos:ajax_buscar_servicios")
        resp = self.client.get(url, {"q": "service"})
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn("results", data)
        texts = [r["text"].lower() for r in data["results"]]
        self.assertTrue(any("brake" in t or "service" in t for t in texts))
        # No debe incluir servicios de otra empresa
        self.assertFalse(any("tire" in t for t in texts))
        # Todos los resultados deben tener id
        for r in data["results"]:
            self.assertIn("id", r)
            self.assertIn("text", r)
