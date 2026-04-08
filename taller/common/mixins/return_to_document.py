from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from django.http import HttpRequest
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


class ReturnToDocumentMixin:
    """
    Mixin para flujos "crear entidad -> volver a documento".

    Admite contrato nuevo:
      - return_to
      - field_target
      - entity_type

    Y mantiene compatibilidad con contrato legacy:
      - next
    """

    return_param_name = "return_to"
    legacy_return_param_name = "next"
    field_target_param = "field_target"
    target_row_param = "target_row"
    fallback_url_name = "documentos:documento_crear"
    entity_type = ""

    def _raw_return_to(self) -> str:
        request = self.request
        return (
            request.POST.get(self.return_param_name)
            or request.GET.get(self.return_param_name)
            or request.POST.get(self.legacy_return_param_name)
            or request.GET.get(self.legacy_return_param_name)
            or ""
        ).strip()

    def get_return_to(self) -> str:
        raw = self._raw_return_to()
        if not raw:
            return self.get_fallback_return_url()

        allowed_hosts = {self.request.get_host()}
        if not url_has_allowed_host_and_scheme(
            raw, allowed_hosts=allowed_hosts, require_https=self.request.is_secure()
        ):
            return self.get_fallback_return_url()

        parsed = urlparse(raw)
        # Normalizar a ruta interna para evitar cambios de host/esquema.
        if parsed.netloc:
            path = parsed.path or "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
            return path
        return raw

    def get_fallback_return_url(self) -> str:
        try:
            return reverse(self.fallback_url_name)
        except Exception:
            return "/"

    def get_field_target(self) -> str:
        request = self.request
        return (
            request.POST.get(self.field_target_param)
            or request.GET.get(self.field_target_param)
            or ""
        ).strip()

    def get_entity_type(self) -> str:
        return self.entity_type or self.get_field_target() or ""

    def get_target_row(self) -> str:
        request = self.request
        return (
            request.POST.get(self.target_row_param) or request.GET.get(self.target_row_param) or ""
        ).strip()

    def get_created_label(self, obj) -> str:
        for attr in ("nombre", "name", "descripcion", "part_number"):
            value = getattr(obj, attr, None)
            if value:
                return str(value)
        return f"#{getattr(obj, 'pk', '')}"

    def get_context_redirect_params(self, obj) -> dict[str, str]:
        params: dict[str, str] = {
            "entity_type": self.get_entity_type(),
            "field_target": self.get_field_target(),
            "target_row": self.get_target_row(),
            "created_id": str(getattr(obj, "pk", "") or ""),
            "created_label": self.get_created_label(obj),
        }
        return {k: v for k, v in params.items() if v not in (None, "")}

    def build_success_url_with_context(self, obj) -> str:
        base_url = self.get_return_to()
        parsed = urlparse(base_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.update(self.get_context_redirect_params(obj))
        return urlunparse(parsed._replace(query=urlencode(query)))

    def get_success_url(self):
        obj = getattr(self, "object", None)
        if obj is None:
            return super().get_success_url()  # pragma: no cover
        return self.build_success_url_with_context(obj)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["return_to"] = self.get_return_to()
        context["field_target"] = self.get_field_target()
        context["target_row"] = self.get_target_row()
        context["is_return_to_document"] = bool(
            self.request.GET.get(self.return_param_name)
            or self.request.GET.get(self.legacy_return_param_name)
            or self.request.POST.get(self.return_param_name)
            or self.request.POST.get(self.legacy_return_param_name)
        )
        return context


def build_return_to_document_url(
    request: HttpRequest,
    *,
    entity_type: str,
    created_id: str | int | None,
    created_label: str,
    field_target: str = "",
) -> str:
    """
    Helper para FBV: compone URL de retorno segura hacia documento.
    """
    raw_return_to = (
        request.POST.get("return_to")
        or request.GET.get("return_to")
        or request.POST.get("next")
        or request.GET.get("next")
        or ""
    ).strip()

    allowed_hosts = {request.get_host()}
    if not raw_return_to or not url_has_allowed_host_and_scheme(
        raw_return_to, allowed_hosts=allowed_hosts, require_https=request.is_secure()
    ):
        try:
            raw_return_to = reverse("documentos:documento_crear")
        except Exception:
            raw_return_to = "/"

    parsed = urlparse(raw_return_to)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    if entity_type:
        query["entity_type"] = entity_type
    if field_target:
        query["field_target"] = field_target
    target_row = (request.POST.get("target_row") or request.GET.get("target_row") or "").strip()
    if target_row:
        query["target_row"] = target_row
    if created_id not in (None, ""):
        query["created_id"] = str(created_id)
    if created_label:
        query["created_label"] = str(created_label)

    return urlunparse(parsed._replace(query=urlencode(query)))
