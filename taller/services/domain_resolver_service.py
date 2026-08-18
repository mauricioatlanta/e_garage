"""
DomainResolverService

Resuelve el tenant a partir del encabezado HTTP Host.

Responsabilidades:
    - Normalizar el host (minúsculas, sin puerto, soporte IPv6).
    - Clasificar si un host puede ser dominio personalizado de un tenant.
    - Consultar EmpresaDominio[estado=ACTIVO] con caché de dos niveles:
        · hit positivo  → TTL 5 min
        · miss negativo → TTL 1 min  (evita stampede en hosts inexistentes)
    - Invalidar la caché cuando el estado de un dominio cambia.

Punto de extensión para fases futuras:
    - Fase 3: SSL/certbot → enganchar en resolve() o en un método propio.
    - Fase 4: branding → DomainResolverService.get_branding(ed).
    - Métricas → decorar get_for_host() con counters.
    El middleware no necesita cambiar para ninguna de esas adiciones.

No contiene lógica de request/response; es agnóstico a Django views.
"""

from django.core.cache import cache

from taller.models.empresa_dominio import EmpresaDominio

# Sentinel que distingue "clave ausente en caché" de "cacheado como None".
# Definido aquí; re-exportado desde host_tenant para compatibilidad con tests.
_SENTINEL = object()

# Hosts propios de la plataforma; jamás tratados como dominio de un tenant.
_PLATFORM_HOSTS = frozenset(
    [
        "egarage.cl",
        "www.egarage.cl",
        "proxy.egarage.cl",
        "api.egarage.cl",
        "app.egarage.cl",
        "mail.egarage.cl",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "[::1]",
    ]
)


class DomainResolverService:
    """Servicio de resolución de tenant por dominio personalizado."""

    CACHE_TTL_HIT  = 300   # segundos — dominio ACTIVO encontrado
    CACHE_TTL_MISS = 60    # segundos — dominio no encontrado

    # ── API pública ───────────────────────────────────────────────────────────

    @classmethod
    def resolve(cls, request) -> "EmpresaDominio | None":
        """
        Punto de entrada principal.

        Devuelve el EmpresaDominio ACTIVO que corresponde al host del request,
        o None si el host es de la plataforma o no tiene dominio activo.
        """
        host = cls.normalize_host(request)
        if not cls.is_custom_host(host):
            return None
        return cls.get_for_host(host)

    @staticmethod
    def normalize_host(request) -> str:
        """Retorna el host HTTP en minúsculas sin número de puerto."""
        host = request.get_host() or ""
        if host.startswith("["):
            # IPv6: [::1]:8000 → [::1]
            bracket_end = host.find("]")
            if bracket_end != -1:
                host = host[:bracket_end + 1]
        elif ":" in host:
            # hostname:puerto → hostname
            host = host.rsplit(":", 1)[0]
        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    @staticmethod
    def is_custom_host(host: str) -> bool:
        """True si el host podría corresponder al dominio personalizado de un tenant."""
        if not host:
            return False
        if host in _PLATFORM_HOSTS:
            return False
        if host.endswith(".egarage.cl"):
            return False
        return True

    @classmethod
    def get_for_host(cls, host: str) -> "EmpresaDominio | None":
        """
        Devuelve el EmpresaDominio ACTIVO para *host*, usando caché.

        Almacena tanto hits positivos como negativos para evitar una SQL por
        request incluso cuando el host no existe.
        """
        cache_key = cls._cache_key(host)
        cached = cache.get(cache_key, _SENTINEL)
        if cached is not _SENTINEL:
            return cached   # None = miss negativo; objeto = hit positivo

        try:
            ed = (
                EmpresaDominio.objects
                .select_related("empresa")
                .get(dominio=host, estado=EmpresaDominio.Estado.ACTIVO)
            )
        except EmpresaDominio.DoesNotExist:
            ed = None

        timeout = cls.CACHE_TTL_HIT if ed is not None else cls.CACHE_TTL_MISS
        cache.set(cache_key, ed, timeout=timeout)
        return ed

    @classmethod
    def invalidate_cache(cls, host: str) -> None:
        """Elimina la entrada de caché para *host*. Llamar tras suspender o activar un dominio."""
        cache.delete(cls._cache_key(host))

    # ── Internos ──────────────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(host: str) -> str:
        return f"custom_domain:{host}"
