from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from taller.tests.factories import EmpresaFactory


class CountryAwareLoginTests(TestCase):
    login_url = "/cl/es/accounts/login/"

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="country-login-user",
            email="country-login@example.com",
            password="StrongPass123!",
        )
        EmpresaFactory(user=self.user, pais="CL", onboarding_completado=True)
        self.payload = {
            "login": self.user.email,
            "password": "StrongPass123!",
        }

    def test_authenticated_get_still_renders_login(self):
        self.client.force_login(self.user)

        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["country"], "CL")

    def test_authenticated_post_processes_credentials(self):
        self.client.force_login(self.user)

        response = self.client.post(self.login_url, self.payload, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/cl/es/workspace/")

    def test_anonymous_post_processes_credentials(self):
        response = self.client.post(self.login_url, self.payload, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/cl/es/workspace/")

    def test_authenticated_login_redirect_setting_remains_disabled(self):
        self.assertFalse(settings.ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS)
