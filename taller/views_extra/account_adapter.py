# taller/auth/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

from django.urls import reverse
from django.utils.translation import activate


class CountryAwareAccountAdapter(DefaultAccountAdapter):
    """
    Decide el redirect post-login según el país, respetando ?next=
    y evitando hardcodes. Usa namespaces: usa:taller:dashboard / chile:taller:dashboard
    """

    COUNTRY_MAP = {
        "US": {"ns": "usa", "lang": "en", "default_url_name": "taller:dashboard"},
        "CL": {"ns": "chile", "lang": "es", "default_url_name": "taller:dashboard"},
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

    def _reverse_by_country(
        self, country_code, view_path="taller:dashboard", *args, **kwargs
    ):
        """
        view_path puede ser 'taller:dashboard' o 'clientes:lista_clientes', etc.
        """
        meta = self.COUNTRY_MAP.get(country_code)
        if not meta:
            # Fallback conservador a CL
            meta = self.COUNTRY_MAP["CL"]
        # Si view_path ya trae subnamespace (p.ej. 'clientes:lista_clientes'), lo respetamos
        if ":" in view_path and not view_path.startswith("taller:"):
            name = f"{meta['ns']}:{view_path}"
        else:
            # 'taller:dashboard' o similar
            name = f"{meta['ns']}:{view_path}"
        return reverse(name, args=args, kwargs=kwargs)

    def get_login_redirect_url(self, request):
        # 0) Respetar ?next= si es seguro/permitido por allauth
        next_url = request.GET.get("next") or request.POST.get("next")
        if next_url and self.is_safe_url(next_url, request.get_host()):
            # Si next_url no empieza por /us/ o /cl/, lo dejamos igual
            # (allauth valida seguridad de la redirección).
            return next_url

        # 1) Empresa del usuario (fuente primaria)
        if request.user.is_authenticated:
            # empresa.pais
            country = self._normalize_country(
                getattr(getattr(request.user, "empresa", None), "pais", None)
            )
            if not country:
                # perfil.pais (secundaria)
                country = self._normalize_country(
                    getattr(getattr(request.user, "perfil", None), "pais", None)
                )
            if country:
                # Setear idioma y sesión
                meta = self.COUNTRY_MAP[country]
                activate(meta["lang"])
                request.session["django_language"] = meta["lang"]
                request.session["country"] = meta["ns"]  # 'usa' o 'chile'
                return self._reverse_by_country(country, "taller:dashboard")

        # 2) request.country (middleware)
        country = self._normalize_country(getattr(request, "country", None))
        if country:
            meta = self.COUNTRY_MAP[country]
            activate(meta["lang"])
            request.session["django_language"] = meta["lang"]
            request.session["country"] = meta["ns"]
            return self._reverse_by_country(country, "taller:dashboard")

        # 3) Parámetros y sesión
        country = self._normalize_country(request.GET.get("country"))
        if not country:
            sess_country_ns = (request.session.get("country") or "").strip().lower()
            # Mapear ns de sesión -> código país
            country = (
                "US"
                if sess_country_ns == "usa"
                else ("CL" if sess_country_ns == "chile" else None)
            )

        if country:
            meta = self.COUNTRY_MAP[country]
            activate(meta["lang"])
            request.session["django_language"] = meta["lang"]
            request.session["country"] = meta["ns"]
            return self._reverse_by_country(country, "taller:dashboard")

        # 4) Path prefix (último recurso)
        path = (request.path or "").strip().lower()
        if path.startswith("/us/") or path == "/us":
            activate("en")
            request.session["django_language"] = "en"
            request.session["country"] = "usa"
            return self._reverse_by_country("US", "taller:dashboard")
        if path.startswith("/cl/") or path == "/cl":
            activate("es")
            request.session["django_language"] = "es"
            request.session["country"] = "chile"
            return self._reverse_by_country("CL", "taller:dashboard")

        # 5) Fallback final a CL (explícito y namespaced)
        activate("es")
        request.session["django_language"] = "es"
        request.session["country"] = "chile"
        return self._reverse_by_country("CL", "taller:dashboard")
