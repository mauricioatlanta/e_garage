from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo


@dataclass(frozen=True)
class DocumentFormMode:
    mode: str
    cliente: Optional[Cliente] = None
    vehiculo: Optional[Vehiculo] = None
    source_document: Optional[Documento] = None

    def __str__(self) -> str:
        return self.mode

    @property
    def is_clean(self) -> bool:
        return self.mode == "clean"

    @property
    def is_prefill(self) -> bool:
        return self.mode == "prefill"

    @property
    def is_duplicate(self) -> bool:
        return self.mode == "duplicate"

    @property
    def is_draft(self) -> bool:
        return self.mode == "draft"

    @property
    def allow_prefetch(self) -> bool:
        return self.mode in {"duplicate", "edit", "draft"}

    @property
    def allow_line_prefill(self) -> bool:
        return self.mode in {"duplicate", "edit", "draft"}


def _safe_cliente_for_user(request, cliente_id):
    if not cliente_id:
        return None
    try:
        return Cliente.objects.for_user(request.user).get(pk=cliente_id)
    except Exception:
        return None


def _safe_vehiculo_for_user(request, vehiculo_id):
    if not vehiculo_id:
        return None
    try:
        return Vehiculo.objects.for_user(request.user).get(pk=vehiculo_id)
    except Exception:
        return None


def resolve_document_form_mode(request, *args, source_document=None, is_edit=False, **kwargs):
    source_draft = kwargs.get("source_draft")
    if source_document is not None:
        return DocumentFormMode(
            mode="duplicate",
            cliente=getattr(source_document, "cliente", None),
            vehiculo=getattr(source_document, "vehiculo", None),
            source_document=source_document,
        )

    if source_draft is not None:
        return DocumentFormMode(mode="draft")

    if is_edit:
        return DocumentFormMode(mode="edit")

    cliente = _safe_cliente_for_user(request, request.GET.get("cliente_id"))
    vehiculo = _safe_vehiculo_for_user(request, request.GET.get("vehiculo_id"))

    if cliente or vehiculo:
        if vehiculo and cliente and getattr(vehiculo, "cliente_id", None) != cliente.id:
            vehiculo = None
        return DocumentFormMode(
            mode="prefill",
            cliente=cliente,
            vehiculo=vehiculo,
        )

    return DocumentFormMode(mode="clean")


# ===== BACKWARD COMPAT =====
FORM_MODE_CLEAN = "clean"
FORM_MODE_PREFILL = "prefill"
FORM_MODE_DUPLICATE = "duplicate"
FORM_MODE_DRAFT = "draft"
FORM_MODE_EDIT = "edit"


def resolve_form_mode(request, *args, **kwargs):
    return resolve_document_form_mode(request, *args, **kwargs)
