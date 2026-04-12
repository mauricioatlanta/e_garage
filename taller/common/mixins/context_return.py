from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def get_safe_context_return_url(request, url: str) -> str:
    """
    Devuelve una URL relativa segura para volver al contexto anterior.
    Rechaza URLs absolutas externas y valores vacíos.
    """
    candidate = (url or "").strip()
    if not candidate:
        return ""

    parsed = urlparse(candidate)

    # Solo permitir rutas relativas internas
    if parsed.scheme or parsed.netloc:
        return ""

    path = parsed.path or "/"
    if not path.startswith("/"):
        return ""

    return urlunparse(("", "", path, "", parsed.query, ""))


def build_context_return_url(base: str, params: dict | None = None) -> str:
    """
    Reaplica parámetros de query sobre una URL base relativa.
    """
    safe_base = (base or "").strip()
    if not safe_base:
        return ""

    parsed = urlparse(safe_base)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    for key, value in (params or {}).items():
        if value is None:
            continue
        query[str(key)] = str(value)

    new_query = urlencode(query, doseq=True)
    return urlunparse(("", "", parsed.path or "/", "", new_query, ""))


class ContextReturnCreateMixin:
    """
    Mixin simple para vistas CreateView que necesiten:
    - exponer return_to al template
    - redirigir al contexto original cuando existe
    """

    context_return_param = "return_to"

    def get_context_return_url(self) -> str:
        getter = getattr(self.request, "GET", {})
        value = getter.get(self.context_return_param) or getter.get("next") or ""
        return get_safe_context_return_url(self.request, value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["context_return_url"] = self.get_context_return_url()
        return context

    def get_success_url(self):
        context_return = self.get_context_return_url()
        if context_return:
            return context_return
        return super().get_success_url()
