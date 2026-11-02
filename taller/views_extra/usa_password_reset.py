"""Vistas allauth para /us/*/accounts/password/* con redirects al namespace usa."""

from django.urls import reverse

from allauth.account.views import PasswordResetFromKeyView, PasswordResetView


class USAPasswordResetView(PasswordResetView):
    def get_success_url(self):
        return reverse("usa:account_reset_password_done")


class USAPasswordResetFromKeyView(PasswordResetFromKeyView):
    def get_success_url(self):
        return reverse("usa:account_reset_password_from_key_done")
