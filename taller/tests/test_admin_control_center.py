from django.test import TestCase
from django.urls import resolve, reverse

from taller.analytics.public_views import public_analytics_dashboard
from taller.qa_control.views import control as qa_control_view
from taller.tests.factories import EmpresaFactory, UserFactory
from taller.views_extra.admin_control import admin_control_center
from taller.views_extra.admin_suscriptores import admin_suscriptores


class AdminControlCenterTests(TestCase):
    def test_anonymous_user_cannot_access(self):
        response = self.client.get(reverse("admin_control_center"))

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(
            response,
            "Centro de Administración eGarage",
            status_code=403,
        )

    def test_normal_user_cannot_access(self):
        user = UserFactory()
        EmpresaFactory(user=user)
        self.client.force_login(user)

        response = self.client.get(reverse("admin_control_center"))

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(
            response,
            "Centro de Administración eGarage",
            status_code=403,
        )

    def test_unauthorized_superuser_cannot_access(self):
        user = UserFactory(email="other@example.com", is_superuser=True)
        EmpresaFactory(user=user)
        self.client.force_login(user)

        response = self.client.get(reverse("admin_control_center"))

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(
            response,
            "Centro de Administración eGarage",
            status_code=403,
        )

    def test_authorized_superuser_can_access(self):
        user = UserFactory(email="mauricioatlanta@gmail.com", is_superuser=True)
        EmpresaFactory(user=user)
        self.client.force_login(user)

        response = self.client.get(reverse("admin_control_center"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/control.html")
        self.assertContains(response, "Centro de Administración eGarage")
        self.assertContains(response, "Torre de Control QA")
        self.assertContains(response, "Inteligencia de Visitas")
        self.assertContains(response, "Gestión de Suscriptores")

    def test_admin_control_links_use_real_routes(self):
        user = UserFactory(email="mauricioatlanta@gmail.com", is_superuser=True)
        EmpresaFactory(user=user)
        self.client.force_login(user)

        response = self.client.get(reverse("admin_control_center"))

        self.assertContains(response, f'href="{reverse("qa_control:control")}"')
        self.assertContains(response, f'href="{reverse("admin_visitas")}"')
        self.assertContains(response, f'href="{reverse("admin_suscriptores")}"')
        self.assertEqual(reverse("qa_control:control"), "/qa/control/")
        self.assertEqual(reverse("admin_visitas"), "/admin/visitas/")
        self.assertEqual(reverse("admin_suscriptores"), "/admin/suscriptores/")

    def test_admin_control_does_not_shadow_django_admin(self):
        self.assertEqual(resolve("/admin/control/").func, admin_control_center)
        self.assertEqual(reverse("admin:index"), "/admin/")

    def test_destination_views_continue_to_resolve(self):
        self.assertEqual(resolve("/qa/control/").func, qa_control_view)
        self.assertEqual(resolve("/admin/visitas/").func, public_analytics_dashboard)
        self.assertEqual(resolve("/admin/suscriptores/").func, admin_suscriptores)
