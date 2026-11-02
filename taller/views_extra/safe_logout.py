from django.contrib.auth import logout as django_logout
from django.http import HttpResponseRedirect
from django.views import View

from allauth.account.adapter import get_adapter
from allauth.account import app_settings as allauth_app_settings


class SafeLogoutView(View):
    """
    Evita SessionInterrupted en Django 4.2 + allauth cuando el flujo de logout
    toca la sesión después de hacer flush().
    """

    http_method_names = ["get", "post", "head", "options"]

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET" and not allauth_app_settings.LOGOUT_ON_GET:
            return HttpResponseRedirect(self._get_redirect_url(request))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self._logout_and_redirect(request)

    def post(self, request, *args, **kwargs):
        return self._logout_and_redirect(request)

    @staticmethod
    def _get_redirect_url(request) -> str:
        next_url = (request.GET.get("next") or request.POST.get("next") or "").strip()
        if next_url:
            return next_url
        return get_adapter(request).get_logout_redirect_url(request)

    def _logout_and_redirect(self, request):
        redirect_url = self._get_redirect_url(request)
        django_logout(request)
        return HttpResponseRedirect(redirect_url)


safe_logout_view = SafeLogoutView.as_view()
