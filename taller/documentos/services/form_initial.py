from __future__ import annotations

from django.utils import timezone


def _build_cliente_state(cliente):
    if not cliente:
        return {
            "id": "",
            "nombre": "",
            "email": "",
            "telefono": "",
        }

    nombre = (
        str(cliente)
        or " ".join(
            part
            for part in [getattr(cliente, "nombre", ""), getattr(cliente, "apellido", "")]
            if part
        ).strip()
        or f"Cliente #{getattr(cliente, 'pk', '')}"
    )

    return {
        "id": str(getattr(cliente, "pk", "") or ""),
        "nombre": nombre,
        "email": getattr(cliente, "email", "") or "",
        "telefono": getattr(cliente, "telefono", "") or "",
    }


def build_form_initial_state(*, form_mode=None, source_document=None, **kwargs):
    mode = kwargs.get("mode", form_mode)
    base_initial = dict(kwargs.get("base_initial", {}) or {})

    initial = {
        "fecha_emision": timezone.now().date(),
    }
    initial.update(base_initial)

    cliente_obj = getattr(mode, "cliente", None) or getattr(source_document, "cliente", None)
    vehiculo_obj = getattr(mode, "vehiculo", None) or getattr(source_document, "vehiculo", None)

    if vehiculo_obj and not cliente_obj:
        cliente_obj = getattr(vehiculo_obj, "cliente", None)

    cliente_data = _build_cliente_state(cliente_obj)
    vehiculo_id = str(getattr(vehiculo_obj, "pk", "") or "")

    if cliente_data["id"]:
        initial.setdefault("cliente", cliente_data["id"])
        initial.setdefault("cliente_id", cliente_data["id"])

    if vehiculo_id:
        initial.setdefault("vehiculo", vehiculo_id)
        initial.setdefault("vehiculo_id", vehiculo_id)

    return {
        "initial": initial,
        "cliente": cliente_data,
        "vehiculo_id": vehiculo_id,
    }
