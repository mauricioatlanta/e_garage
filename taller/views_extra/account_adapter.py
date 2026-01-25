# taller/auth/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

from django.urls import reverse
from django.utils.translation import activate


class CountryAwareAccountAdapter(DefaultAccountAdapter):
    """
    Adaptador que permite login a superusuarios sin verificación de email
    """

    def is_open_for_signup(self, request):
        """Permitir registro"""
        return True

    def pre_authenticate(self, request, **credentials):
        """Permitir autenticación a superusuarios sin verificación de email"""
        login = credentials.get("username") or credentials.get("email") or credentials.get("login")
        if login:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                # Buscar usuario por username o email
                user = User.objects.filter(username=login).first()
                if not user:
                    user = User.objects.filter(email=login).first()

                # Si es superuser o staff, permitir login sin verificación
                if user and (user.is_superuser or user.is_staff):
                    # Marcar para saltar verificación
                    credentials["skip_email_verification"] = True
                    return credentials
            except Exception:
                pass
        return credentials

    def is_open_for_signup(self, request):
        """Permitir registro"""
        return True

    def can_authenticate(self, request, email_address):
        """Permitir autenticación a superusuarios sin verificación"""
        user = email_address.user
        if user and (user.is_superuser or user.is_staff):
            return True
        return super().can_authenticate(request, email_address)

    def get_login_redirect_url(self, request):
        """Redirigir admin al admin después del login"""
        # Si el usuario es superuser y viene del admin, redirigir al admin
        if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url and "/admin/" in next_url:
                return next_url
            elif "/admin/" in request.path:
                return "/admin/"
        # Usar la lógica original de country-aware
        return super().get_login_redirect_url(request)

    def is_email_verified(self, request, email_address):
        """Permitir login a superusuarios sin verificación de email"""
        user = email_address.user
        if user and (user.is_superuser or user.is_staff):
            return True
        return super().is_email_verified(request, email_address)

    """
    Decide el redirect post-login según el país, respetando ?next=
    y evitando hardcodes. Usa namespaces: usa:dashboard / chile:dashboard
    """

    COUNTRY_MAP = {
        "US": {"ns": "usa", "lang": "en", "default_url_name": "dashboard"},
        "CL": {"ns": "chile", "lang": "es", "default_url_name": "dashboard"},
    }

    def _normalize_country(self, value):
        if not value:
            return None
        v = str(value).strip().upper()
        if v in ("US", "USA"):
            return "US"
        if v in ("CL", "CHILE"):
            return "CL"
        return None

    def _reverse_by_country(self, country_code, view_path="dashboard", *args, **kwargs):
        """
        view_path puede ser 'dashboard' o 'clientes:lista_clientes', etc.
        Si view_path contiene ':', se asume que ya incluye el namespace completo.
        Si no, se construye como {country_ns}:{view_path}
        """
        meta = self.COUNTRY_MAP.get(country_code)
        if not meta:
            # Fallback conservador a CL
            meta = self.COUNTRY_MAP["CL"]

        # Si view_path ya trae namespace completo (p.ej. 'taller_cl:dashboard' o 'clientes:lista_clientes'), lo respetamos
        if ":" in view_path:
            name = view_path
        else:
            # Construir como {country_ns}:{view_path}
            name = f"{meta['ns']}:{view_path}"

        url = reverse(name, args=args, kwargs=kwargs)
        print(
            f"[CountryAwareAccountAdapter] _reverse_by_country: country={country_code}, view_path={view_path}, name={name}, url={url}"
        )
        return url

    def get_login_redirect_url(self, request):
        print(f"[CountryAwareAccountAdapter] get_login_redirect_url iniciado")
        print(f"[CountryAwareAccountAdapter] Path: {request.path}")
        print(f"[CountryAwareAccountAdapter] User authenticated: {request.user.is_authenticated}")
        print(f"[CountryAwareAccountAdapter] User: {request.user}")

        # 0) Respetar ?next= si es seguro/permitido por allauth
        next_url = request.GET.get("next") or request.POST.get("next")
        print(f"[CountryAwareAccountAdapter] Next URL: {next_url}")

        if next_url and self.is_safe_url(next_url, request.get_host()):
            print(f"[CountryAwareAccountAdapter] ✅ Redirigiendo a next_url (seguro): {next_url}")
            return next_url
        elif next_url:
            print(f"[CountryAwareAccountAdapter] ⚠️ Next URL no es seguro, ignorando: {next_url}")

        # 1) Empresa del usuario (fuente primaria)
        if request.user.is_authenticated:
            empresa = getattr(request.user, "empresa", None)
            empresa_pais = getattr(empresa, "pais", None) if empresa else None
            print(f"[CountryAwareAccountAdapter] Empresa: {empresa}, País empresa: {empresa_pais}")

            # empresa.pais
            country = self._normalize_country(empresa_pais)
            print(f"[CountryAwareAccountAdapter] Country from empresa: {country}")

            if not country:
                # perfil.pais (secundaria)
                perfil = getattr(request.user, "perfil", None)
                perfil_pais = getattr(perfil, "pais", None) if perfil else None
                print(f"[CountryAwareAccountAdapter] Perfil: {perfil}, País perfil: {perfil_pais}")
                country = self._normalize_country(perfil_pais)
                print(f"[CountryAwareAccountAdapter] Country from perfil: {country}")

            if country:
                # Setear idioma y sesión
                meta = self.COUNTRY_MAP[country]
                activate(meta["lang"])
                request.session["django_language"] = meta["lang"]
                request.session["country"] = meta["ns"]  # 'usa' o 'chile'
                print(
                    f"[CountryAwareAccountAdapter] ✅ Redirigiendo a dashboard de {country} (desde empresa/perfil)"
                )
                return self._reverse_by_country(country, "dashboard")

        # 2) request.country (middleware)
        request_country = getattr(request, "country", None)
        print(f"[CountryAwareAccountAdapter] request.country: {request_country}")
        country = self._normalize_country(request_country)
        if country:
            meta = self.COUNTRY_MAP[country]
            activate(meta["lang"])
            request.session["django_language"] = meta["lang"]
            request.session["country"] = meta["ns"]
            print(
                f"[CountryAwareAccountAdapter] ✅ Redirigiendo a dashboard de {country} (desde request.country)"
            )
            return self._reverse_by_country(country, "dashboard")

        # 3) Parámetros y sesión
        country_param = request.GET.get("country")
        print(f"[CountryAwareAccountAdapter] GET country param: {country_param}")
        country = self._normalize_country(country_param)

        if not country:
            sess_country_ns = (request.session.get("country") or "").strip().lower()
            print(f"[CountryAwareAccountAdapter] Session country: {sess_country_ns}")
            # Mapear ns de sesión -> código país
            country = (
                "US" if sess_country_ns == "usa" else ("CL" if sess_country_ns == "chile" else None)
            )
            print(f"[CountryAwareAccountAdapter] Country from session: {country}")

        if country:
            meta = self.COUNTRY_MAP[country]
            activate(meta["lang"])
            request.session["django_language"] = meta["lang"]
            request.session["country"] = meta["ns"]
            print(
                f"[CountryAwareAccountAdapter] ✅ Redirigiendo a dashboard de {country} (desde params/session)"
            )
            return self._reverse_by_country(country, "dashboard")

        # 4) Path prefix (último recurso)
        path = (request.path or "").strip().lower()
        print(f"[CountryAwareAccountAdapter] Path prefix check: {path}")
        if path.startswith("/us/") or path == "/us":
            activate("en")
            request.session["django_language"] = "en"
            request.session["country"] = "usa"
            print(
                f"[CountryAwareAccountAdapter] ✅ Redirigiendo a dashboard US (desde path prefix)"
            )
            return self._reverse_by_country("US", "dashboard")
        if path.startswith("/cl/") or path == "/cl":
            activate("es")
            request.session["django_language"] = "es"
            request.session["country"] = "chile"
            print(
                f"[CountryAwareAccountAdapter] ✅ Redirigiendo a dashboard CL (desde path prefix)"
            )
            return self._reverse_by_country("CL", "dashboard")

        # 5) Fallback final a CL (explícito y namespaced)
        activate("es")
        request.session["django_language"] = "es"
        request.session["country"] = "chile"
        print(f"[CountryAwareAccountAdapter] ✅ Redirigiendo a dashboard CL (fallback final)")
        return self._reverse_by_country("CL", "dashboard")
