import ipaddress
from urllib.parse import urlparse
from django.conf import settings


CANONICAL_PUBLIC_HOSTS = frozenset({"egarage.cl", "www.egarage.cl"})

SCANNER_PATH_TOKENS = (
    "/wp-admin",
    "/wp-login",
    "xmlrpc.php",
    ".env",
    "setup.php",
    "phpinfo",
    "/vendor/phpunit",
    "/.git",
    "/adminer",
    "/boaform",
)

SCANNER_USER_AGENT_TOKENS = (
    "curl",
    "python-requests",
    "python-urllib",
    "zgrab",
    "censys",
    "masscan",
    "nmap",
    "nikto",
    "sqlmap",
    "wget",
    "go-http-client",
    "httpx",
)


def normalize_host(host: str) -> str:
    host = (host or "").strip().lower()
    if not host:
        return ""
    if host.startswith("[") and "]" in host:
        return host[1:host.index("]")]
    return host.split(":", 1)[0]


def is_raw_ip_host(host: str) -> bool:
    normalized = normalize_host(host)
    if not normalized:
        return True
    try:
        ipaddress.ip_address(normalized)
        return True
    except ValueError:
        return False


def is_canonical_public_host(host: str) -> bool:
    return normalize_host(host) in CANONICAL_PUBLIC_HOSTS


def is_allowed_public_analytics_host(host: str) -> bool:
    """Canonical hosts in production; local test hosts only while DEBUG is on."""
    normalized = normalize_host(host)
    if normalized in CANONICAL_PUBLIC_HOSTS:
        return True
    return bool(getattr(settings, "DEBUG", False) and normalized in {"testserver", "localhost", "127.0.0.1"})


def classify_traffic_channel(referrer: str = "", utm_source: str = "") -> str:
    """Returns a stable commercial channel instead of exposing raw URLs."""
    src = (utm_source or "").strip().lower()
    ref = (referrer or "").strip().lower()
    haystack = src
    if haystack:
        for keys, label in ((
            (("fb", "facebook", "meta"), "FACEBOOK"),
            (("ig", "instagram"), "INSTAGRAM"),
            (("tt", "tiktok"), "TIKTOK"),
            (("goog", "google", "adwords", "cpc"), "GOOGLE"),
            (("wa", "whatsapp"), "WHATSAPP"),
        )):
            if any(key in haystack for key in keys):
                return label
        return f"CAMPAÑA ({src.upper()[:40]})"
    if ref:
        try:
            domain = urlparse(ref).netloc.lower()
        except Exception:
            domain = ref
        for keys, label in ((
            (("google.com", "google.cl", "google."), "GOOGLE"),
            (("facebook.com", "m.facebook.com", "l.facebook.com", "fb.me"), "FACEBOOK"),
            (("instagram.com", "l.instagram.com"), "INSTAGRAM"),
            (("tiktok.com", "link.tiktok.com"), "TIKTOK"),
            (("whatsapp.com", "api.whatsapp.com", "web.whatsapp.com", "wa.me"), "WHATSAPP"),
        )):
            if any(key in domain for key in keys):
                return label
        if any(key in domain for key in ("egarage.cl", "localhost", "127.0.0.1")):
            return "INTERNO"
        return "OTRO_REFERRER"
    return "DIRECTO"


def is_scanner_path(path: str) -> bool:
    normalized = (path or "").lower()
    return any(token in normalized for token in SCANNER_PATH_TOKENS)


def is_scanner_user_agent(user_agent: str) -> bool:
    ua = (user_agent or "").strip().lower()
    if not ua:
        return True
    return any(token in ua for token in SCANNER_USER_AGENT_TOKENS)


def is_probable_non_human_request(request, user_agent: str | None = None) -> bool:
    host = ""
    if request is not None:
        try:
            host = request.get_host()
        except Exception:
            host = getattr(request, "META", {}).get("HTTP_HOST", "")
    ua = user_agent if user_agent is not None else getattr(request, "META", {}).get("HTTP_USER_AGENT", "")
    path = getattr(request, "path", "") if request is not None else ""
    return (
        not is_allowed_public_analytics_host(host)
        or (is_raw_ip_host(host) and not (getattr(settings, "DEBUG", False) and normalize_host(host) == "127.0.0.1"))
        or is_scanner_path(path)
        or is_scanner_user_agent(ua)
    )
