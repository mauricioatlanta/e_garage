"""
Vista de login directo para admin que bypassa allauth
"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages


@method_decorator(csrf_exempt, name="dispatch")
class AdminDirectLoginView(LoginView):
    """
    Vista de login directo para admin que bypassa allauth
    Solo permite login a usuarios que sean staff o superuser
    """

    template_name = "admin/login_direct.html"

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        # Intentar autenticación con username
        user = authenticate(self.request, username=username, password=password)

        # Si no funciona con username, intentar con email
        if not user:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(self.request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user and (user.is_staff or user.is_superuser):
            login(self.request, user)
            messages.success(self.request, f"Bienvenido, {user.username}")
            return redirect("/admin/")
        else:
            messages.error(
                self.request, "Credenciales inválidas o usuario no tiene permisos de admin"
            )
            return redirect("/admin/login-direct/")

    def get_success_url(self):
        return "/admin/"


def admin_direct_login(request):
    """Función wrapper para la vista de login directo"""
    view = AdminDirectLoginView.as_view()
    return view(request)
