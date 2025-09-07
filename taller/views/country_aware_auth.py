from allauth.account.views import LoginView


class CountryAwareLoginView(LoginView):
    """
    Vista de login que detecta el país desde el parámetro 'next'
    para asegurar el contexto correcto de país
    """

    def dispatch(self, request, *args, **kwargs):
        # Detectar país desde next parameter si está disponible
        next_url = request.GET.get("next", "")
        if next_url:
            if next_url.startswith("/us/"):
                request.country = "US"
                request.country_code = "US"
            elif next_url.startswith("/cl/"):
                request.country = "CL"
                request.country_code = "CL"

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Asegurar que el contexto de país está disponible
        next_url = self.request.GET.get("next", "")
        if next_url.startswith("/us/"):
            context["country"] = "US"
            context["current_country"] = "usa"
        elif next_url.startswith("/cl/"):
            context["country"] = "CL"
            context["current_country"] = "chile"
        else:
            # Por defecto Chile
            context["country"] = "CL"
            context["current_country"] = "chile"

        return context


# Vista funcional como alternativa
def country_aware_login(request):
    """
    Vista funcional de login que detecta país desde múltiples fuentes:
    1. Parámetro 'next' en URL
    2. Usuario autenticado (empresa/perfil)
    3. Parámetro 'country' en URL
    4. Por defecto Chile
    """
    next_url = request.GET.get("next", "")
    country_param = request.GET.get("country", "")

    # PRIORIDAD 1: Detectar país desde next parameter
    if next_url.startswith("/us/"):
        request.country = "US"
        request.country_code = "US"
    elif next_url.startswith("/cl/"):
        request.country = "CL"
        request.country_code = "CL"

    # PRIORIDAD 2: Detectar país desde parámetro country
    elif country_param.upper() in ["US", "USA"]:
        request.country = "US"
        request.country_code = "US"
    elif country_param.upper() in ["CL", "CHILE"]:
        request.country = "CL"
        request.country_code = "CL"

    # PRIORIDAD 3: Si el usuario ya está autenticado, usar su país
    elif request.user.is_authenticated:
        try:
            # Buscar en empresa
            if hasattr(request.user, "empresa") and hasattr(
                request.user.empresa, "pais"
            ):
                request.country = request.user.empresa.pais
                request.country_code = request.user.empresa.pais
            # Buscar en perfil
            elif hasattr(request.user, "perfil") and hasattr(
                request.user.perfil, "pais"
            ):
                request.country = request.user.perfil.pais
                request.country_code = request.user.perfil.pais
            else:
                # Por defecto Chile si no hay información
                request.country = "CL"
                request.country_code = "CL"
        except:
            request.country = "CL"
            request.country_code = "CL"

    # PRIORIDAD 4: Por defecto Chile
    else:
        request.country = "CL"
        request.country_code = "CL"

    # Usar la vista original de allauth con contexto corregido
    from allauth.account.views import login as allauth_login

    return allauth_login(request)
