class CountryAwareLoginView:
    """
    Vista de login que detecta el país desde el parámetro 'next'
    para asegurar el contexto correcto de país

    # SAFE IMPORT: No importa modelos a nivel de módulo para evitar AppRegistryNotReady
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

    # PRIORIDAD 3: Detectar desde sesión (preferencia guardada)
    elif request.session.get("preferred_country"):
        saved_country = request.session.get("preferred_country", "").upper()
        if saved_country in ["US", "USA"]:
            request.country = "US"
            request.country_code = "US"
        elif saved_country in ["CL", "CHILE"]:
            request.country = "CL"
            request.country_code = "CL"
        else:
            request.country = "CL"
            request.country_code = "CL"

    # PRIORIDAD 4: Detectar desde HTTP_REFERER (de dónde viene el usuario)
    elif request.headers.get("referer"):
        referer = request.headers.get("referer", "")
        if "/us/" in referer or "/usa/" in referer:
            request.country = "US"
            request.country_code = "US"
        elif "/cl/" in referer or "/chile/" in referer:
            request.country = "CL"
            request.country_code = "CL"
        else:
            request.country = "CL"
            request.country_code = "CL"

    # PRIORIDAD 5: Si el usuario ya está autenticado, usar su país
    elif request.user.is_authenticated:
        try:
            # Buscar en empresa
            if hasattr(request.user, "empresa") and hasattr(request.user.empresa, "pais"):
                request.country = request.user.empresa.pais
                request.country_code = request.user.empresa.pais
            # Buscar en perfil
            elif hasattr(request.user, "perfil") and hasattr(request.user.perfil, "pais"):
                request.country = request.user.perfil.pais
                request.country_code = request.user.perfil.pais
            else:
                # Por defecto Chile si no hay información
                request.country = "CL"
                request.country_code = "CL"
        except:
            request.country = "CL"
            request.country_code = "CL"

    # PRIORIDAD 6: Por defecto Chile
    else:
        request.country = "CL"
        request.country_code = "CL"

    # Guardar preferencia en sesión para futuras visitas
    request.session["preferred_country"] = request.country

    # Usar la vista original de allauth con contexto corregido
    from allauth.account.views import login as allauth_login

    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.forms.custom_login import CustomLoginForm

    # Asegurar que el formulario se pase correctamente
    if request.method == "GET":
        form = CustomLoginForm()
    else:
        form = CustomLoginForm(request.POST)

    # Llamar a la vista de allauth
    response = allauth_login(request)

    # Si es una respuesta de template, asegurar que el formulario esté en el contexto
    if hasattr(response, "context_data"):
        response.context_data["form"] = form
        response.context_data["debug"] = True  # Para debugging

        # Forzar el template correcto basado en el país detectado
        country = getattr(request, "country", "CL")
        lang = get_language() or "es"

        if country == "US":
            # Para USA, usar template específico en inglés
            if lang == "es":
                # Si se selecciona español, usar template de Chile
                template_name = "taller/cl/es/account/login.html"
            else:
                # Por defecto inglés para USA
                template_name = "taller/us/en/account/login.html"
        else:
            # Para Chile, usar template específico
            if lang == "en":
                # No existe template en inglés para Chile, usar el de USA
                template_name = "taller/us/en/account/login.html"
            else:
                # Por defecto español para Chile
                template_name = "taller/cl/es/account/login.html"

        # Crear nueva respuesta con el template correcto
        context = response.context_data.copy()
        context["form"] = form
        context["country"] = country
        context["LANGUAGE_CODE"] = lang

        return TemplateResponse(request, template_name, context)

    return response
