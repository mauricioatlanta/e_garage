from allauth.account.views import SignupView

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.utils.translation import activate

from taller.forms.custom_signup import CustomSignupForm


class CustomSignupView(SignupView):
    """
    Vista de registro personalizada que maneja la selección de país
    y redirige al usuario a la sección correspondiente
    """

    form_class = CustomSignupForm
    template_name = "account/signup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Account - eGarage"
        context["is_universal_signup"] = True
        return context

    def form_valid(self, form):
        # Obtener el país seleccionado
        country = form.cleaned_data.get("country", "US")

        # Guardar el usuario
        user = form.save(self.request)

        # Configurar idioma basado en el país
        if country == "CL":
            activate("es")
            self.request.session["django_language"] = "es"
            self.request.session["country"] = "chile"
        else:  # US
            activate("en")
            self.request.session["django_language"] = "en"
            self.request.session["country"] = "usa"

        # Hacer login del usuario con backend explícito
        # Django necesita saber qué backend usar cuando hay múltiples configurados
        backend = settings.AUTHENTICATION_BACKENDS[0]  # Usar el primer backend (ModelBackend)
        user.backend = backend
        login(self.request, user, backend=backend)

        # Mensaje de éxito
        if country == "CL":
            messages.success(
                self.request, "¡Cuenta creada exitosamente! Bienvenido a eGarage Chile."
            )
        else:
            messages.success(self.request, "Account created successfully! Welcome to eGarage USA.")

        # Redirigir según el país
        if country == "CL":
            return redirect("chile:centro_operaciones")
        else:
            return redirect("usa:centro_operaciones_espacial")

    def form_invalid(self, form):
        # Mantener el idioma seleccionado en caso de error
        country = self.request.POST.get("country", "US")
        if country == "CL":
            activate("es")
        else:
            activate("en")
        return super().form_invalid(form)
