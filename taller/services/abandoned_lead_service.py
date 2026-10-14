from taller.models.abandoned_lead import AbandonedLead
from taller.utils.smart_logging import get_client_ip


def _clean(value: str, limit: int) -> str:
    return (value or "").strip()[:limit]


def capture_abandoned_lead(request, payload: dict) -> tuple[AbandonedLead | None, bool]:
    email = _clean(payload.get("email", ""), 254).lower()
    whatsapp = _clean(payload.get("whatsapp", "") or payload.get("telefono", ""), 32)
    if not email and not whatsapp:
        return None, False

    defaults = {
        "nombre": _clean(payload.get("nombre", ""), 160),
        "rubro": _clean(payload.get("rubro", ""), 80),
        "pais": _clean(payload.get("pais", ""), 8).upper(),
        "ip_address": get_client_ip(request) or None,
    }

    qs = AbandonedLead.objects.all()
    lead = None
    if email:
        lead = qs.filter(email=email).first()
    if lead is None and whatsapp:
        lead = qs.filter(whatsapp=whatsapp).first()

    if lead is None:
        lead = AbandonedLead.objects.create(email=email, whatsapp=whatsapp, **defaults)
        return lead, True

    changed = []
    for field, value in {"email": email, "whatsapp": whatsapp, **defaults}.items():
        if value and getattr(lead, field) != value:
            setattr(lead, field, value)
            changed.append(field)
    if changed:
        lead.save(update_fields=[*changed, "updated_at"])
    return lead, False
