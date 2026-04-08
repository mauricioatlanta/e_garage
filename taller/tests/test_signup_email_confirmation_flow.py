import re

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail


User = get_user_model()


@pytest.mark.django_db
class TestSignupEmailConfirmationFlow:
    @pytest.fixture(autouse=True)
    def _email_confirmation_settings(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        settings.ACCOUNT_CONFIRM_EMAIL_ON_GET = True
        settings.ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
        settings.ACCOUNT_RATE_LIMITS = {"confirm_email": "1000/m"}
        settings.DEFAULT_FROM_EMAIL = "support@egarage.cl"
        # En settings_prod puede venir True y forzar 301 a https://testserver/...
        # Para estos tests de flujo de auth necesitamos evaluar la vista sin ese redirect.
        settings.SECURE_SSL_REDIRECT = False

    def _signup_payload(self, email, country, telefono):
        return {
            "email": email,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "telefono": telefono,
            "country": country,
        }

    def _extract_confirmation_link(self, body):
        match = re.search(r"https?://[^\s]+/confirm-email/[^\s]+", body)
        assert match, "No se encontro enlace de confirmacion en el correo"
        return match.group(0).rstrip(").,")

    def test_get_signup_chile_ok(self, client):
        response = client.get("/cl/es/accounts/signup/")
        assert response.status_code == 200

    def test_signup_chile_requires_email_confirmation(self, client):
        response = client.post(
            "/cl/es/accounts/signup/",
            self._signup_payload("flow-cl@example.com", "CL", "+56911112222"),
        )

        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated
        assert User.objects.filter(email="flow-cl@example.com").exists()
        assert "Te enviamos un correo de confirmacion" in response.content.decode()
        assert len(mail.outbox) == 1
        assert "support@egarage.cl" in mail.outbox[0].from_email

        confirm_link = self._extract_confirmation_link(mail.outbox[0].body)
        assert "/cl/es/accounts/confirm-email/" in confirm_link

        confirm_response = client.get(confirm_link, follow=True)
        assert confirm_response.redirect_chain
        assert confirm_response.redirect_chain[-1][0].startswith("/cl/es/")
        assert "_auth_user_id" in client.session

    def test_signup_usa_requires_email_confirmation(self, client):
        response = client.post(
            "/us/signup/",
            self._signup_payload("flow-us@example.com", "US", "+13055550101"),
            follow=True,
        )

        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated
        assert User.objects.filter(email="flow-us@example.com").exists()
        assert "Te enviamos un correo de confirmacion" in response.content.decode()
        assert len(mail.outbox) == 1

        confirm_link = self._extract_confirmation_link(mail.outbox[0].body)
        assert "/us/en/accounts/confirm-email/" in confirm_link

        confirm_response = client.get(confirm_link, follow=True)
        assert confirm_response.redirect_chain
        assert confirm_response.redirect_chain[-1][0].startswith("/us/")
        assert "_auth_user_id" in client.session

    def test_login_and_password_reset_endpoints_still_work(self, client):
        user = User.objects.create_user(
            username="login-check@example.com",
            email="login-check@example.com",
            password="StrongPass123!",
        )

        login_response = client.post(
            "/cl/es/accounts/login/",
            {"login": user.email, "password": "StrongPass123!"},
            follow=False,
        )
        assert login_response.status_code in (302, 303)

        reset_cl = client.get("/cl/es/accounts/password/reset/")
        assert reset_cl.status_code == 200

        reset_us = client.get("/us/accounts/password/reset/")
        assert reset_us.status_code in (301, 302)

    def test_login_form_keeps_country_aware_action(self, client):
        response = client.get("/cl/es/accounts/login/")

        assert response.status_code == 200
        content = response.content.decode()
        assert 'action="/cl/es/accounts/login/"' in content
        assert 'action="/accounts/login/"' not in content

    def test_verified_login_redirect_stays_inside_country_prefix(self, client):
        user = User.objects.create_user(
            username="verified-login@example.com",
            email="verified-login@example.com",
            password="StrongPass123!",
        )
        EmailAddress.objects.create(
            user=user,
            email="verified-login@example.com",
            verified=True,
            primary=True,
        )

        response = client.post(
            "/cl/es/accounts/login/",
            {"login": user.email, "password": "StrongPass123!"},
            follow=False,
        )

        assert response.status_code in (302, 303)
        assert response.headers["Location"].startswith("/cl/es/")

    def test_invalid_confirmation_redirects_to_country_aware_login(self, client):
        session = client.session
        session["pending_signup_country"] = "US"
        session["pending_signup_lang"] = "en"
        session.save()

        response = client.get("/accounts/confirm-email/invalid-key/", follow=False)

        assert response.status_code in (302, 303)
        assert response.headers["Location"] == "/us/en/accounts/login/"
