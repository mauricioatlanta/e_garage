from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.services.subscription_access_service import SubscriptionAccessService


class SubscriptionAccessServiceTests(TestCase):
    def setUp(self):
        self._user_index = 0

    def _create_empresa(self, *, days_offset: int, suscripcion_activa: bool, pais: str = "CL"):
        self._user_index += 1
        user = User.objects.create_user(
            username=f"subscription-user-{self._user_index}",
            email=f"subscription-user-{self._user_index}@test.com",
            password="testpass123",
        )
        empresa = Empresa.objects.create(
            user=user,
            nombre_taller=f"Taller {self._user_index}",
            pais=pais,
        )
        empresa.fecha_fin = timezone.now() + timedelta(days=days_offset)
        empresa.suscripcion_activa = suscripcion_activa
        empresa.save()
        return empresa

    def test_active_allows_servicios_get(self):
        empresa = self._create_empresa(days_offset=10, suscripcion_activa=True)

        decision = SubscriptionAccessService.decide(empresa, "/cl/es/servicios/", "GET")

        self.assertEqual(decision.state, "active")
        self.assertTrue(decision.allow)
        self.assertFalse(decision.warn)

    def test_grace_allows_servicios_get_with_warning(self):
        empresa = self._create_empresa(days_offset=-2, suscripcion_activa=False)

        decision = SubscriptionAccessService.decide(empresa, "/cl/es/servicios/", "GET")

        self.assertEqual(decision.state, "grace")
        self.assertTrue(decision.allow)
        self.assertTrue(decision.warn)

    def test_restricted_allows_servicios_get_with_warning(self):
        empresa = self._create_empresa(days_offset=-10, suscripcion_activa=False)

        decision = SubscriptionAccessService.decide(empresa, "/cl/es/servicios/", "GET")

        self.assertEqual(decision.state, "restricted")
        self.assertTrue(decision.allow)
        self.assertTrue(decision.warn)
        self.assertEqual(decision.reason, "restricted_soft")

    def test_restricted_blocks_servicios_post(self):
        empresa = self._create_empresa(days_offset=-10, suscripcion_activa=False)

        decision = SubscriptionAccessService.decide(empresa, "/cl/es/servicios/", "POST")

        self.assertEqual(decision.state, "restricted")
        self.assertFalse(decision.allow)
        self.assertEqual(decision.redirect_to, "/cl/es/suscripcion/pago/")
        self.assertEqual(decision.reason, "restricted_write_block")

    def test_restricted_blocks_dashboard_get(self):
        empresa = self._create_empresa(days_offset=-10, suscripcion_activa=False)

        decision = SubscriptionAccessService.decide(empresa, "/cl/es/dashboard/", "GET")

        self.assertEqual(decision.state, "restricted")
        self.assertFalse(decision.allow)
        self.assertEqual(decision.redirect_to, "/cl/es/suscripcion/pago/")
        self.assertEqual(decision.reason, "restricted_hard")

    def test_blocked_redirects_soft_module_get(self):
        empresa = self._create_empresa(days_offset=-45, suscripcion_activa=False)

        decision = SubscriptionAccessService.decide(empresa, "/cl/es/servicios/", "GET")

        self.assertEqual(decision.state, "blocked")
        self.assertFalse(decision.allow)
        self.assertEqual(decision.redirect_to, "/cl/es/suscripcion/pago/")
        self.assertEqual(decision.reason, "blocked_soft")

    def test_exempt_billing_path_keeps_real_state(self):
        empresa = self._create_empresa(days_offset=-45, suscripcion_activa=False, pais="US")

        decision = SubscriptionAccessService.decide(
            empresa,
            "/us/en/subscription/payment/",
            "GET",
        )

        self.assertEqual(decision.state, "blocked")
        self.assertTrue(decision.allow)
        self.assertTrue(decision.warn)
        self.assertEqual(decision.redirect_to, None)

    def test_billing_url_is_country_aware(self):
        empresa = self._create_empresa(days_offset=-10, suscripcion_activa=False, pais="US")

        billing_url = SubscriptionAccessService.get_billing_url(empresa)

        self.assertEqual(billing_url, "/us/en/subscription/payment/")
