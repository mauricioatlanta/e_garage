# taller/views_extra/account_adapter.py
import logging

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from urllib.parse import quote

from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from allauth.utils import build_absolute_uri
from django.utils.translation import activate

logger = logging.getLogger(__name__)


class CountryAwareAccountAdapter(DefaultAccountAdapter):
    """
    Adaptador que permite login a superusuarios sin verificacion de email
    y gestiona redirecciones por pais para el proyecto e_garage.
    """

    def add_message(self, request, level, *args, **kwargs):
        """
        No encolar mensajes de sesión iniciada/cerrada: suelen amontonarse con otros
        flashes y molestan en login / primer pantallazo del workspace.
        """
        first = args[0] if args else None
        mt = str(first or "").replace("\\", "/").lower()
        if "logged_in" in mt or "logged_out" in mt:
            return
        return super().add_message(request, level, *args, **kwargs)

    def get_client_ip(self, request) -> str:
        """
        Fallback robusto para producción detrás de nginx/gunicorn.
        Evita que allauth lance PermissionDenied si no logra resolver IP.
        """
        meta = request.META

        xff = (meta.get("HTTP_X_FORWARDED_FOR") or "").strip()
        if xff:
            ip = xff.split(",")[0].strip()
            if ip:
                logger.info(
                    "LOGIN IP via X_FORWARDED_FOR | ip=%s path=%s host=%s",
                    ip,
                    request.path,
                    request.get_host(),
                )
                return ip

        real_ip = (meta.get("HTTP_X_REAL_IP") or "").strip()
        if real_ip:
            logger.info(
                "LOGIN IP via X_REAL_IP | ip=%s path=%s host=%s",
                real_ip,
                request.path,
                request.get_host(),
            )
            return real_ip

        remote_addr = (meta.get("REMOTE_ADDR") or "").strip()
        if remote_addr:
            logger.info(
                "LOGIN IP via REMOTE_ADDR | ip=%s path=%s host=%s",
                remote_addr,
                request.path,
                request.get_host(),
            )
            return remote_addr

        logger.error(
            "LOGIN IP NOT FOUND | path=%s host=%s meta_keys=%s",
            request.path,
            request.get_host(),
            sorted(meta.keys()),
        )
        return "127.0.0.1"

    def is_open_for_signup(self, request):
        return True

    def can_authenticate(self, request, email_address):
        user = getattr(email_address, "user", None)
        if user and (user.is_superuser or user.is_staff):
            return True
        return super().can_authenticate(request, email_address)

    def is_email_verified(self, request, email_address):
        user = getattr(email_address, "user", None)
        if user and (user.is_superuser or user.is_staff):
            return True
        return super().is_email_verified(request, email_address)

    def get_reset_password_from_key_url(self, key):
        """
        Genera URL de reset con contexto de país/idioma para evitar perder routing.
        El enlace del mail debe apuntar a la misma jerarquía que usó el usuario.
        """
        req = getattr(self, "request", None)

        # Determinar país/idioma desde request o usuario
        country, lang = self._country_lang_from_request_or_user(request=req)

        # Mapeo de países a namespaces
        namespace_map = {
            "CL": "chile",
            "US": "usa",
            "MX": "mexico",
            "AR": "argentina",
            "UY": "uruguay",
            "PE": "peru",
            "CO": "colombia",
            "EC": "ecuador",
            "VE": "venezuela",
        }

        namespace = namespace_map.get(country, "chile")

        try:
            # Intentar generar URL con namespace del país
            p = reverse(
                f"{namespace}:account_reset_password_from_key",
                kwargs={"uidb36": "UID", "key": "KEY"},
            )
            p = p.replace("UID-KEY", quote(key, safe=""))
            url = build_absolute_uri(req, p)
            logger.info(
                "PASSWORD RESET URL generada | country=%s lang=%s namespace=%s url=%s",
                country,
                lang,
                namespace,
                url,
            )
            return url
        except Exception as e:
            logger.warning(
                "PASSWORD RESET URL fallback | country=%s namespace=%s error=%s",
                country,
                namespace,
                e,
            )
            # Fallback a comportamiento por defecto de Allauth
            return super().get_reset_password_from_key_url(key)

    def get_password_change_redirect_url(self, request):
        if (request.path or "").startswith("/cl/es/"):
            return reverse("chile:account_change_password")
        return super().get_password_change_redirect_url(request)

    def _country_lang_from_request_or_user(self, request=None, user=None):
        country = None
        if user is not None:
            empresa = getattr(user, "empresa", None)
            country = self._normalize_country(getattr(empresa, "pais", None)) if empresa else None
        if not country and request is not None:
            path = (request.path or "").lower()
            if path.startswith("/us/"):
                country = "US"
            elif path.startswith("/cl/"):
                country = "CL"
            if not country:
                session_country = self._normalize_country(
                    request.session.get("pending_signup_country")
                    or request.session.get("country")
                    or request.GET.get("country")
                )
                country = session_country
        if not country:
            country = "CL"
        lang = "en" if country == "US" else "es"
        return country, lang

    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        Genera enlace de confirmacion con contexto de pais/idioma para no perder routing.
        """
        user = getattr(getattr(emailconfirmation, "email_address", None), "user", None)
        country, lang = self._country_lang_from_request_or_user(request=request, user=user)
        path = f"/{country.lower()}/{lang}/accounts/confirm-email/{emailconfirmation.key}/"
        return build_absolute_uri(request, path)

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Fuerza activate_url country-aware en el email de confirmacion.
        """
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_site": get_current_site(request),
            "key": emailconfirmation.key,
            "request": request,
            "email": emailconfirmation.email_address.email,
        }
        if signup:
            template = "account/email/email_confirmation_signup"
        else:
            template = "account/email/email_confirmation"
        self.send_mail(template, emailconfirmation.email_address.email, ctx)

    def send_mail(self, template_prefix, email, context):
        """
        En producción no se silencian errores SMTP:
        se registran y se propagan para que el monitoreo detecte el fallo real.
        """
        try:
            sent = super().send_mail(template_prefix, email, context)
            if sent == 0:
                logger.warning(
                    "PASSWORD RESET / EMAIL: No se envió ningún correo (backend devolvió 0). "
                    "Revisar SMTP (EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD) y logs del backend. to=%s",
                    email,
                )
            return sent
        except Exception as e:
            logger.exception(
                "Error enviando email (template=%s, to=%s): %s.",
                template_prefix,
                email,
                e,
            )
            suppress_errors = getattr(
                settings,
                "ACCOUNT_ADAPTER_SUPPRESS_EMAIL_ERRORS",
                False,
            )
            if suppress_errors:
                logger.error(
                    "ACCOUNT_ADAPTER_SUPPRESS_EMAIL_ERRORS=True: se suprime excepción de email."
                )
                return 0
            raise

    COUNTRY_MAP = {
        "US": {"ns": "usa", "lang": "en", "default_url_name": "centro_trabajo"},
        "CL": {"ns": "chile", "lang": "es", "default_url_name": "centro_trabajo"},
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

    def _reverse_by_country(self, country_code, view_path="centro_operaciones", *args, **kwargs):
        meta = self.COUNTRY_MAP.get(country_code) or self.COUNTRY_MAP["CL"]

        if ":" in view_path:
            name = view_path
        else:
            name = f"{meta['ns']}:{view_path}"

        return reverse(name, args=args, kwargs=kwargs)

    def get_logout_redirect_url(self, request):
        """
        Redirigir al login correcto según país al cerrar sesión.
        Se llama ANTES del logout, cuando el usuario aún está autenticado.
        Evita que suscriptores USA terminen en /cl/es/accounts/login/.
        """
        country = None
        # PRIORIDAD 1: Usuario autenticado (empresa/perfil)
        if request.user.is_authenticated:
            try:
                empresa = getattr(request.user, "empresa", None)
                if empresa and hasattr(empresa, "pais"):
                    country = self._normalize_country(empresa.pais)
                if not country:
                    perfil = getattr(request.user, "perfil", None)
                    if perfil and hasattr(perfil, "pais"):
                        country = self._normalize_country(perfil.pais)
            except Exception:
                pass
        # PRIORIDAD 2: Path actual (/us/en/workspace/ → US)
        if not country:
            path = (request.path or "").lower()
            if path.startswith("/us") or path.startswith("/usa"):
                country = "US"
            elif path.startswith("/cl"):
                country = "CL"
            elif path.startswith("/mx"):
                country = "MX"
        # PRIORIDAD 3: Sesión (antes de que allauth la limpie)
        if not country:
            sess = (request.session.get("country") or "").strip().lower()
            if sess in ("us", "usa"):
                country = "US"
            elif sess in ("cl", "chile"):
                country = "CL"
            elif sess in ("mx", "mexico"):
                country = "MX"
        # PRIORIDAD 4: Referer (path /accounts/logout/ no tiene país; el Referer sí)
        if not country:
            ref = (request.headers.get("referer") or "").lower()
            if "/us" in ref or "/usa" in ref:
                country = "US"
            elif "/cl" in ref or "/chile" in ref:
                country = "CL"
            elif "/mx" in ref:
                country = "MX"
        # Redirigir al login del país
        if country == "US":
            try:
                return reverse("usa:account_login")
            except Exception:
                return "/us/en/accounts/login/"
        if country == "MX":
            try:
                return reverse("mexico:account_login")
            except Exception:
                return "/mx/es/accounts/login/"
        # Chile por defecto
        try:
            return reverse("chile:account_login")
        except Exception:
            return "/cl/es/accounts/login/"

    def get_login_redirect_url(self, request):
        try:
            if request.user.is_authenticated and (
                request.user.is_superuser or request.user.is_staff
            ):
                next_url = request.GET.get("next") or request.POST.get("next")
                if next_url and "/admin/" in next_url:
                    return next_url
                elif "/admin/" in request.path:
                    return "/admin/"

            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                next_clean = (next_url or "").strip().rstrip("/") or "/"
                if (
                    next_clean in ("/us", "/us/", "/cl", "/cl/")
                    or next_clean.startswith("/us?")
                    or next_clean.startswith("/cl?")
                ):
                    pass
                else:
                    return next_url

            # Prioridad: (1) empresa/perfil si autenticado (2) URL actual (3) sesión (4) request.country (5) GET (6) CL.
            # USA subscriber usando /cl/accounts/login/ debe ir a /us/en/workspace/, no Chile.
            country = None
            path = (request.path or "").lower()

            # PRIORIDAD 1: Usuario autenticado - país de su empresa (USA subscriber → USA workspace)
            if request.user.is_authenticated:
                empresa = getattr(request.user, "empresa", None)
                country = (
                    self._normalize_country(getattr(empresa, "pais", None)) if empresa else None
                )
                if not country:
                    perfil = getattr(request.user, "perfil", None)
                    country = (
                        self._normalize_country(getattr(perfil, "pais", None)) if perfil else None
                    )

            # PRIORIDAD 2: Path actual (/us/login/ → US)
            if not country and path.startswith("/us/"):
                country = "US"
            elif not country and path.startswith("/cl/"):
                country = "CL"

            # PRIORIDAD 3: Sesión
            if not country:
                session_country = (request.session.get("country") or "").strip().upper()
                if session_country in ("US", "USA"):
                    country = "US"
                elif session_country in ("CL",):
                    country = "CL"

            # PRIORIDAD 4: request.country (middleware)
            if not country:
                country = self._normalize_country(getattr(request, "country", None))

            # PRIORIDAD 5: GET country
            if not country:
                country = self._normalize_country(request.GET.get("country"))

            if not country:
                country = "CL"

            if country == "US":
                meta_us = self.COUNTRY_MAP["US"]
                activate(meta_us["lang"])
                try:
                    request.session["django_language"] = meta_us["lang"]
                    request.session["country"] = meta_us["ns"]
                except Exception:
                    pass
                try:
                    return reverse("us_en:centro_trabajo")
                except Exception:
                    return "/us/en/workspace/"

            meta = self.COUNTRY_MAP.get(country, self.COUNTRY_MAP["CL"])
            activate(meta["lang"])

            try:
                request.session["django_language"] = meta["lang"]
                request.session["country"] = meta["ns"]
            except Exception:
                pass

            default_view = meta.get("default_url_name", "centro_operaciones")
            try:
                return self._reverse_by_country(country, default_view)
            except Exception:
                if country == "US":
                    return "/us/en/workspace/"
                return "/cl/es/workspace/"
        except Exception:
            # No caer siempre en Chile: usar path/sesión para decidir destino.
            try:
                path = (request.path or "").lower()
                if path.startswith("/us/"):
                    return "/us/en/workspace/"
                if (request.session.get("country") or "").strip().lower() in ("us", "usa"):
                    return "/us/en/workspace/"
            except Exception:
                pass
            try:
                return self._reverse_by_country("CL", "centro_trabajo")
            except Exception:
                return "/cl/es/workspace/"
