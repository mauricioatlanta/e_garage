from allauth.account.adapter import DefaultAccountAdapter


class CountryAwareAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        # PRIORIDAD 1: Detectar país desde usuario autenticado (empresa)
        if request.user.is_authenticated:
            try:
                # Buscar en empresa (prioridad más alta)
                if hasattr(request.user, "empresa") and hasattr(
                    request.user.empresa, "pais"
                ):
                    if request.user.empresa.pais == "US":
                        return "/us/en/dashboard/"  # Ambiente de trabajo del usuario
                    elif request.user.empresa.pais == "CL":
                        return "/cl/dashboard/"  # Ambiente de trabajo del usuario
                # Buscar en perfil
                elif hasattr(request.user, "perfil") and hasattr(
                    request.user.perfil, "pais"
                ):
                    if request.user.perfil.pais == "US":
                        return "/us/en/dashboard/"  # Ambiente de trabajo del usuario
                    elif request.user.perfil.pais == "CL":
                        return "/cl/dashboard/"  # Ambiente de trabajo del usuario
            except:
                pass

        # PRIORIDAD 2: Detectar país desde request.country (seteado por middleware/vista)
        if hasattr(request, "country"):
            if request.country == "US":
                return "/us/en/dashboard/"  # Ambiente de trabajo del usuario
            elif request.country == "CL":
                return "/cl/dashboard/"  # Ambiente de trabajo del usuario

        # PRIORIDAD 3: Detectar país por path o parámetros
        path = request.path
        if path.startswith("/cl/") or "cl" in request.GET.get("country", ""):
            return "/cl/dashboard/"  # Ambiente de trabajo del usuario
        if (
            path.startswith("/us")
            or path.startswith("/usa")
            or "us" in request.GET.get("country", "")
            or "usa" in request.GET.get("country", "")
        ):
            return "/us/en/dashboard/"  # Ambiente de trabajo del usuario
        country = request.session.get("country")
        if country == "usa":
            return "/us/en/dashboard/"  # Ambiente de trabajo del usuario
        return "/cl/dashboard/"  # Ambiente de trabajo del usuario
