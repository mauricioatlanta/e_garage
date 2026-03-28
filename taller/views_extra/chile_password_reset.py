"""Vistas allauth para /cl/es/accounts/password/* con redirects al namespace chile."""

from django.urls import reverse

from allauth.account.views import PasswordResetFromKeyView, PasswordResetView


class ChilePasswordResetView(PasswordResetView):
    def get_success_url(self):
        return reverse("chile:account_reset_password_done")


class ChilePasswordResetFromKeyView(PasswordResetFromKeyView):
    def get_success_url(self):
        return reverse("chile:account_reset_password_from_key_done")
