"""
Middleware para detectar y armonizar contexto de país con redirección segura.

Jerarquía de detección:
1. Prefijo de URL: /us, /cl (y mapeos legacy /en → /us, /es → /cl)
2. Subdominio: us.*, cl.*
3. Empresa de usuario autenticado
4. (futuro) GeoIP
5. DEFAULT_COUNTRY

Características:
  ✅ Whitelist de rutas (static/media/admin/webhooks)
  ✅ Canonicalización automática: /es/ → /cl/, /en/ → /us/
  ✅ Regex robusto (sin slicing frágil)
  ✅ Manejo seguro de POST (307 para mantener método/body)
  ✅ Prevención de bucles de redirección
  ✅ request.country + request._country_source para debug
"""

import re

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

# =========================
# Constantes
# =========================

COUNTRY_CL = "CL"
COUNTRY_US = "US"

# Prefijos canónicos por país
COUNTRY_PREFIX = {
    COUNTRY_CL: "/cl",
    COUNTRY_US: "/us",
}

# Prefijos legacy → país (para canonicalización automática)
LEGACY_TO_COUNTRY = {
    "/es": COUNTRY_CL,
    "/en": COUNTRY_US,
}

# Rutas que NO deben ser redirigidas (whitelist)
COUNTRY_REDIRECT_WHITELIST = (
    r"^/static/.*",
    r"^/media/.*",
    r"^/admin/.*",
    r"^/favicon\.ico$",
    r"^/robots\.txt$",
    r"^/healthz$",
    r"^/status$",
    r"^/webhooks?/.*",
    r"^/__debug__/.*",  # Django Debug Toolbar
    r"^/api/public/.*",  # APIs públicas sin país
)

_whitelist_compiled = [re.compile(p) for p in COUNTRY_REDIRECT_WHITELIST]


def _is_whitelisted(path: str) -> bool:
    """Verifica si una ruta está en la whitelist y no debe ser tocada."""
    return any(p.match(path) for p in _whitelist_compiled)


# =========================
# Middleware Principal
# =========================


class CountryContextMiddleware(MiddlewareMixin):
    """
    Detección y armonización de país con redirección segura y canónica.

    Flujo:
      1. Detecta país desde múltiples fuentes (URL > subdominio > usuario > default)
      2. Verifica conflictos entre URL y empresa del usuario
      3. Canonicaliza rutas legacy (/es → /cl, /en → /us)
      4. Setea request.country y request._country_source

    Seguridad:
      - Whitelist para rutas estáticas/admin/webhooks
      - Uso de regex para evitar slicing frágil
      - Prevención de bucles con short-circuit
      - POST seguro con 307 (mantiene método/body)
    """

    def process_request(self, request):
        path = request.path

        # Whitelist: No tocar rutas estáticas/admin/webhooks
        if _is_whitelisted(path):
            request.country = getattr(settings, "DEFAULT_COUNTRY", COUNTRY_CL)
            request._country_source = "whitelist"
            return None

        # 1) Detectar país desde URL (incluyendo legacy)
        url_country, url_prefix = self._detect_country_from_url(path)

        # 2) Detectar país desde subdominio
        subd_country = self._detect_country_from_subdomain(request)

        # 3) Detectar país desde empresa del usuario
        user_country = self._detect_country_from_user(request)

        # Resolución preliminar (prefer URL if present)
        country = url_country or subd_country or user_country
        if not country:
            country = self._detect_country_from_ip(request) or getattr(
                settings, "DEFAULT_COUNTRY", COUNTRY_CL
            )

        request.country = country
        request._country_source = (
            "url"
            if url_country
            else ("subdomain" if subd_country else ("user" if user_country else "default"))
        )

        # ----- Conflicto URL vs empresa -----
        # Si la URL dice CL pero la empresa es US (o viceversa), redirigir
        if url_country and user_country and url_country != user_country:
            # Política para POST/PUT/PATCH:
            # Opción A: NO redirigir (confiar en URL para esta request)
            # Opción B: Redirigir con 307 (mantiene método/body)

            # Usando Opción B (estricto multi-tenant)
            if request.method in ("POST", "PUT", "PATCH"):
                return self._redirect_conflict(
                    request, from_country=url_country, to_country=user_country, code=307
                )
            else:
                return self._redirect_conflict(
                    request, from_country=url_country, to_country=user_country, code=302
                )

        # ----- Canonicalizar legacy (/es, /en) → (/cl, /us) -----
        if url_prefix in LEGACY_TO_COUNTRY:
            canonical = COUNTRY_PREFIX[LEGACY_TO_COUNTRY[url_prefix]]
            # Evitar bucles: si ya estamos en la ruta canónica, no hacer nada
            if not path.startswith(canonical + "/") and path != canonical:
                new_url = self._swap_prefix(path, from_prefix=url_prefix, to_prefix=canonical)
                if request.GET:
                    new_url += "?" + request.GET.urlencode()

                if getattr(settings, "DEBUG", False):
                    print(f"🔄 Canonical Redirect: {path} → {new_url} ({url_prefix} → {canonical})")

                # 301 (permanente) para SEO
                resp = HttpResponseRedirect(new_url)
                resp.status_code = 301
                return resp

        # Debug temporal
        if getattr(settings, "DEBUG", False):
            print(f"🌍 CountryContext: {country} (source: {request._country_source}, path: {path})")

        return None

    # =========================
    # Helpers de Detección
    # =========================

    def _detect_country_from_url(self, path: str):
        """
        Detecta país desde prefijo de URL.

        Returns:
            tuple: (country, prefix_detectado) o (None, None)

        Soporta:
          - Canónicos: /cl, /us
          - Legacy: /es (→ CL), /en (→ US)
        """
        lowered = path.lower()

        # Canónicos
        for prefix, ctry in (("/cl", COUNTRY_CL), ("/us", COUNTRY_US)):
            if lowered == prefix or lowered.startswith(prefix + "/"):
                return ctry, prefix

        # Legacy (para canonicalización posterior)
        for legacy_prefix, ctry in LEGACY_TO_COUNTRY.items():
            if lowered == legacy_prefix or lowered.startswith(legacy_prefix + "/"):
                return ctry, legacy_prefix

        return None, None

    def _detect_country_from_subdomain(self, request):
        """
        Detecta país desde subdominio: us.* o cl.*

        Cubre casos como:
          - us.local:8000
          - cl.miapp.com
          - us.staging.miapp.com
        """
        host = request.get_host().lower()  # incluye puerto si lo hay

        if host.startswith("us."):
            return COUNTRY_US
        if host.startswith("cl."):
            return COUNTRY_CL

        return None

    def _detect_country_from_user(self, request):
        """
        Detecta país desde configuración del usuario/empresa.

        Jerarquía:
          0. Empresa activa en sesión (empresa_id)
          1. user.empresa.pais
          2. user.perfil.pais
        """
        u = getattr(request, "user", None)
        if not u or not getattr(u, "is_authenticated", False):
            return None

        try:
            # 0) Prioridad: empresa activa en sesión
            empresa_id = request.session.get("empresa_id")
            if empresa_id:
                try:
                    from taller.models import Empresa

                    emp = Empresa.objects.filter(id=empresa_id).only("id", "pais").first()
                    if emp and getattr(emp, "pais", None):
                        pais = (emp.pais or "").strip().upper()
                        if pais in (COUNTRY_CL, COUNTRY_US):
                            return pais
                except Exception:
                    pass

            # Empresa tiene prioridad
            if hasattr(u, "empresa") and hasattr(u.empresa, "pais"):
                pais = (u.empresa.pais or "").strip().upper()
                return pais if pais in (COUNTRY_CL, COUNTRY_US) else None

            # Fallback a perfil
            if hasattr(u, "perfil") and hasattr(u.perfil, "pais"):
                pais = (u.perfil.pais or "").strip().upper()
                return pais if pais in (COUNTRY_CL, COUNTRY_US) else None
        except Exception:
            return None

        return None

    def _detect_country_from_ip(self, request):
        """
        Detecta país desde geolocalización de IP (último recurso).

        TODO: Implementar con GeoIP2 o servicio externo
        """
        # Placeholder para futura implementación
        # ip = self._get_client_ip(request)
        # return geoip_service.get_country(ip)
        return None

    # =========================
    # Helpers de Redirección
    # =========================

    def _redirect_conflict(self, request, from_country: str, to_country: str, code: int = 302):
        """
        Maneja conflictos entre país de URL y país de empresa.

        Args:
            request: HttpRequest
            from_country: País detectado en URL (ej: "US")
            to_country: País correcto de la empresa (ej: "CL")
            code: Código HTTP (302=temporal, 307=mantiene método POST)

        Returns:
            HttpResponseRedirect con el código especificado
        """
        path = request.path
        from_prefix = COUNTRY_PREFIX.get(from_country, f"/{from_country.lower()}")
        to_prefix = COUNTRY_PREFIX.get(to_country, f"/{to_country.lower()}")

        new_url = self._swap_prefix(path, from_prefix, to_prefix)

        # Preservar query string
        if request.GET:
            new_url += "?" + request.GET.urlencode()

        if getattr(settings, "DEBUG", False):
            print(
                f"🔄 Country Conflict Redirect({code}): {path} → {new_url}  [{from_country} → {to_country}]"
            )

        resp = HttpResponseRedirect(new_url)
        resp.status_code = code  # 302/307
        return resp

    @staticmethod
    def _swap_prefix(path: str, from_prefix: str, to_prefix: str) -> str:
        """
        Reemplaza el prefijo de país de forma segura usando regex.

        Ejemplos:
          /cl         → /us
          /cl/        → /us/
          /cl/vehiculos → /us/vehiculos
          /es/taller  → /cl/taller

        Si la ruta no tiene el prefijo de origen, lo inyecta:
          /vehiculos  → /us/vehiculos

        Args:
            path: Ruta actual
            from_prefix: Prefijo a reemplazar (ej: "/cl")
            to_prefix: Prefijo nuevo (ej: "/us")

        Returns:
            Nueva ruta con el prefijo cambiado
        """
        # Normaliza
        if not from_prefix.startswith("/"):
            from_prefix = "/" + from_prefix
        if not to_prefix.startswith("/"):
            to_prefix = "/" + to_prefix

        # ^/(cl)(/|$)  → reemplaza por /us\1
        # Usa (?P<rest>...) para capturar el resto
        patt = re.compile(rf"^({re.escape(from_prefix)})(?P<rest>/.*|$)", re.IGNORECASE)
        m = patt.match(path)

        if not m:
            # Si no hay prefijo de origen, inyecta el nuevo al inicio
            rest = path if path.startswith("/") else "/" + path
            return f"{to_prefix}{rest}"

        rest = m.group("rest") or ""
        return f"{to_prefix}{rest}"


# =========================
# Middleware de Idioma
# =========================


class LanguageContextMiddleware(MiddlewareMixin):
    """
    Middleware que detecta idioma preferido del usuario.
    Se ejecuta después de CountryContextMiddleware.

    Jerarquía:
      1. Configuración de usuario (user.perfil.idioma_preferido)
      2. Prefijo de URL (/en/, /es/)
      3. País del contexto (US → "en", CL → "es")
      4. Header Accept-Language
    """

    def process_request(self, request):
        language = self._detect_language_from_user(request)

        if not language:
            language = self._detect_language_from_url(request)

        if not language:
            # Fallback basado en país
            country = getattr(request, "country", COUNTRY_CL)
            language = "en" if country == COUNTRY_US else "es"

        if not language:
            # Último recurso: Accept-Language header
            language = self._detect_language_from_header(request)

        request.preferred_language = language or "es"

        # Debug temporal
        if getattr(settings, "DEBUG", False):
            print(
                f"🗣️  LanguageContext: {request.preferred_language} "
                f"(País: {getattr(request, 'country', 'N/A')})"
            )

        return None

    def _detect_language_from_user(self, request):
        """Detecta idioma desde configuración del usuario."""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        try:
            if hasattr(request.user, "perfil") and hasattr(request.user.perfil, "idioma_preferido"):
                return request.user.perfil.idioma_preferido
        except AttributeError:
            pass

        return None

    def _detect_language_from_url(self, request):
        """Detecta idioma desde prefijo de URL (compatibilidad temporal)."""
        path = request.path.lower()

        # Legacy: /en/, /es/
        if re.match(r"^/en(/|$)", path):
            return "en"
        elif re.match(r"^/es(/|$)", path):
            return "es"

        # Canónicos: /us/ → en, /cl/ → es
        if re.match(r"^/us(/|$)", path):
            return "en"
        elif re.match(r"^/cl(/|$)", path):
            return "es"

        return None

    def _detect_language_from_header(self, request):
        """Detecta idioma desde Accept-Language header."""
        accept_lang = request.headers.get("accept-language", "")
        if accept_lang:
            # Simplificado: toma el primer idioma
            lang = accept_lang.lower().split(",")[0].split(";")[0].strip()
            if lang.startswith("en"):
                return "en"
            elif lang.startswith("es"):
                return "es"
        return None
