from __future__ import annotations

from django.db.models import Q


def _normalized(value):
    return (value or "").strip().lower()


def can_start_trial(empresa=None, user=None):
    """
    Soft trial eligibility check.

    Returns (allowed, reason). Missing identity data is treated as allowed so
    existing onboarding flows keep working without adding payment friction.
    """
    from taller.models.empresa import Empresa

    email = _normalized(getattr(empresa, "email", "") or getattr(user, "email", ""))
    telefono = _normalized(getattr(empresa, "telefono", ""))

    if empresa is not None:
        if bool(getattr(empresa, "trial_already_used", False)):
            return False, "trial_already_used"
        if bool(getattr(empresa, "ha_usado_prueba", False)):
            return False, "ha_usado_prueba"
        plan = _normalized(getattr(empresa, "plan", ""))
        if bool(getattr(empresa, "is_trial", False)) or plan == "trial":
            return False, "trial_in_progress"

    if not email and not telefono:
        return True, "identity_missing"

    filters = Q()
    if email:
        filters |= Q(email__iexact=email) | Q(user__email__iexact=email)
    if telefono:
        filters |= Q(telefono__iexact=telefono)

    if not filters:
        return True, "identity_missing"

    queryset = Empresa.objects.filter(filters).filter(
        Q(trial_already_used=True) | Q(ha_usado_prueba=True)
    )
    if empresa is not None and getattr(empresa, "pk", None):
        queryset = queryset.exclude(pk=empresa.pk)

    if queryset.exists():
        return False, "trial_used_by_identity"

    return True, "eligible"
