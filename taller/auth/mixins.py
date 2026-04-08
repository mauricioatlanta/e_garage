# taller/auth/mixins.py

from urllib.parse import quote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from taller.utils.country import prefix_from_path


class CountryLoginRequiredMixin(LoginRequiredMixin):
    """
    Mixin que reemplaza LoginRequiredMixin pero decide login_url según prefijo país+idioma (/cl/es/, /us/en/, etc.).
    """

    def handle_no_permission(self):
        prefix = prefix_from_path(self.request.path)
        login_url = f"/{prefix}/accounts/login/" if prefix else "/accounts/login/"
        next_url = self.request.get_full_path()
        return redirect(f"{login_url}?next={quote(next_url)}")
