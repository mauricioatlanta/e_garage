from taller.services.subscription_access_service import SubscriptionAccessService


def _empty_notice():
    return {
        "subscription_notice": {
            "show": False,
            "level": "info",
            "days_left": None,
            "message": "",
            "renew_url": "",
        }
    }


def _get_empresa(request):
    empresa = getattr(request, "empresa", None)
    if empresa is not None:
        return empresa

    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return None

    try:
        return user.empresa
    except Exception:
        return None


def subscription_notice(request):
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return _empty_notice()

    empresa = _get_empresa(request)
    if empresa is None:
        return _empty_notice()

    renew_url = SubscriptionAccessService.get_billing_url(empresa)
    state = SubscriptionAccessService.get_state(empresa)

    try:
        days_left = int(getattr(empresa, "dias_restantes", 0) or 0)
    except Exception:
        days_left = 0

    notice = {
        "show": False,
        "level": "info",
        "days_left": days_left,
        "message": "",
        "renew_url": renew_url,
    }

    if state == "active":
        if days_left > 7:
            return {"subscription_notice": notice}

        if 3 <= days_left <= 7:
            notice.update(
                {
                    "show": True,
                    "level": "info",
                    "message": (
                        "Tu suscripción vence pronto. Puedes renovarla cuando quieras "
                        "para mantener tu taller activo."
                    ),
                }
            )
            return {"subscription_notice": notice}

        if 1 <= days_left <= 2:
            notice.update(
                {
                    "show": True,
                    "level": "warning",
                    "message": (
                        f"Tu suscripción vence en {days_left} día(s). Renueva en unos "
                        "segundos y sigue trabajando sin interrupciones."
                    ),
                }
            )
            return {"subscription_notice": notice}

        return {"subscription_notice": notice}

    if state == "grace":
        notice.update(
            {
                "show": True,
                "level": "grace",
                "message": (
                    "Tu suscripción venció recientemente. Aún puedes acceder mientras "
                    "regularizas tu renovación."
                ),
            }
        )
        return {"subscription_notice": notice}

    if state in {"restricted", "blocked"}:
        notice.update(
            {
                "show": True,
                "level": "blocked",
                "message": (
                    "Para proteger tu información y mantener tu servicio activo, "
                    "necesitamos que renueves tu suscripción."
                ),
            }
        )
        return {"subscription_notice": notice}

    return {"subscription_notice": notice}
